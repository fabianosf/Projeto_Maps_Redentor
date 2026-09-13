import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Loader2 } from 'lucide-react';
import { getGuia, iniciarTrechoGuia } from '@/api/guia';
import { ApiRequestError } from '@/api/client';
import { DsAlert } from '@/components/auth/DsAlert';
import { FormField } from '@/components/FormField';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuth } from '@/context/AuthContext';
import type { Guia, GuiaTrecho, GuiaViagemCard } from '@/types/guia';

function agoraHHMM(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function agoraLabel(): string {
  const d = new Date();
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function extractHHMM(value?: string | null): string {
  if (!value) return '';
  const m = String(value).match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : '';
}

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  viagem: GuiaViagemCard | null;
  /** Devolve o foco ao botão acionador ao fechar. */
  triggerRef?: React.RefObject<HTMLElement | null>;
  onSuccess: () => void;
  onTrocaMotorista: (guia: Guia, viagem: GuiaViagemCard) => void;
};

/**
 * Painel contextual de Registrar saída — vínculos da operação + SAÍDA real.
 * Não solicita matrícula manual; motorista vem da escala/guia.
 */
export function RegistrarSaidaPanel({
  open,
  onOpenChange,
  viagem,
  triggerRef,
  onSuccess,
  onTrocaMotorista,
}: Props) {
  const titleId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);
  const { user } = useAuth();

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [guia, setGuia] = useState<Guia | null>(null);
  const [trecho, setTrecho] = useState<GuiaTrecho | null>(null);
  const [horSaida, setHorSaida] = useState(agoraHHMM());
  const [erro, setErro] = useState<string | null>(null);

  const despachante = useMemo(() => {
    const mat = user?.matricula?.trim();
    const nome = user?.nome?.trim();
    if (mat && nome) return `${mat} — ${nome}`;
    return nome || mat || 'Usuário autenticado';
  }, [user]);

  const motoristaLabel = useMemo(() => {
    const mat =
      viagem?.matricula_motorista ||
      guia?.matricula_motorista ||
      '';
    const nome = viagem?.motorista || guia?.motorista_nome || '';
    if (mat && nome) return `${mat} — ${nome}`;
    return nome || mat || '';
  }, [guia, viagem]);

  const bloqueios = useMemo(() => {
    const msgs: string[] = [];
    if (!viagem) return ['Viagem não selecionada.'];
    if (viagem.id_trecho == null && !trecho) {
      msgs.push('Trecho operacional não encontrado para esta viagem.');
    }
    const st = String(trecho?.status || viagem.trecho_status || '').toUpperCase();
    if (st && st !== 'PLANEJADO') {
      msgs.push('A viagem não está apta para registrar saída (status diferente de planejado).');
    }
    if (String(guia?.status || '').toUpperCase() === 'ENCERRADA') {
      msgs.push('A guia está encerrada.');
    }
    if (!motoristaLabel) {
      msgs.push(
        'Não há motorista ativo vinculado ao carro nesta escala/turno.',
      );
    }
    const carro = viagem.numero_frota || viagem.veiculo || guia?.numero_frota;
    if (!carro || carro === '—') {
      msgs.push('Carro da viagem não definido.');
    }
    const dispM = guia?.motorista_disponibilidade;
    if (
      dispM?.disponibilidade === 'EM_TRANSITO' &&
      dispM.id_trecho_em_transito != null &&
      dispM.id_trecho_em_transito !== (trecho?.id_trecho ?? viagem.id_trecho)
    ) {
      msgs.push('Motorista já está em trânsito em outra viagem.');
    }
    const dispV = guia?.veiculo_disponibilidade;
    if (
      dispV?.disponibilidade === 'EM_TRANSITO' &&
      dispV.id_trecho_em_transito != null &&
      dispV.id_trecho_em_transito !== (trecho?.id_trecho ?? viagem.id_trecho)
    ) {
      msgs.push('Carro já está em trânsito em outra viagem.');
    }
    return msgs;
  }, [guia, motoristaLabel, trecho, viagem]);

  const podeConfirmar = bloqueios.length === 0 && Boolean(horSaida.trim());

  useEffect(() => {
    if (!open || !viagem?.id_guia) {
      setGuia(null);
      setTrecho(null);
      setErro(null);
      return;
    }
    let alive = true;
    setLoading(true);
    setErro(null);
    setHorSaida(agoraHHMM());
    void (async () => {
      try {
        const data = await getGuia(viagem.id_guia!);
        if (!alive) return;
        setGuia(data.guia);
        const trechos = data.guia.trechos ?? [];
        let match: GuiaTrecho | undefined;
        if (viagem.id_trecho != null) {
          match = trechos.find((t) => t.id_trecho === viagem.id_trecho);
        }
        if (!match) {
          const sent = viagem.sentido.toUpperCase();
          match = trechos.find(
            (t) => String(t.sentido || '').toUpperCase() === sent,
          );
        }
        setTrecho(match ?? null);
        if (match?.hor_ini) {
          const hh = extractHHMM(match.hor_ini);
          if (hh) setHorSaida(hh);
        }
      } catch (err) {
        if (!alive) return;
        setErro(
          err instanceof ApiRequestError
            ? err.message
            : 'Não foi possível carregar os vínculos da operação.',
        );
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [open, viagem]);

  const handleOpenChange = useCallback(
    (next: boolean) => {
      onOpenChange(next);
      if (!next) {
        window.setTimeout(() => {
          triggerRef?.current?.focus();
        }, 0);
      }
    },
    [onOpenChange, triggerRef],
  );

  const confirmar = async () => {
    if (!podeConfirmar || !viagem || submitting) return;
    const idTrecho = trecho?.id_trecho ?? viagem.id_trecho;
    if (idTrecho == null) return;
    setSubmitting(true);
    setErro(null);
    try {
      await iniciarTrechoGuia(idTrecho, {
        hor_ini: horSaida.trim(),
        versao: trecho?.versao ?? viagem.trecho_versao ?? undefined,
      });
      handleOpenChange(false);
      onSuccess();
    } catch (err) {
      setErro(
        err instanceof ApiRequestError
          ? err.message
          : 'Não foi possível registrar a saída.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const linha =
    viagem?.linha ||
    viagem?.codigo_linha ||
    guia?.linha_codigo ||
    guia?.linha_descricao ||
    '—';
  const empresa = viagem?.empresa || guia?.empresa_descricao || '—';
  const carro = viagem?.numero_frota || viagem?.veiculo || guia?.numero_frota || '—';

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-[400px] gap-0 p-0"
        aria-labelledby={titleId}
        onOpenAutoFocus={(e) => {
          e.preventDefault();
          window.setTimeout(() => confirmRef.current?.focus(), 0);
        }}
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          triggerRef?.current?.focus();
        }}
      >
        <DialogHeader className="border-b border-field px-5 py-4 text-left">
          <DialogTitle id={titleId}>Registrar saída</DialogTitle>
          <DialogDescription>
            Confira os vínculos da operação e a saída real. O motorista vem da
            escala — sem digitar matrícula.
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-[60dvh] space-y-3 overflow-y-auto px-5 py-4">
          {loading ? (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Carregando vínculos…
            </p>
          ) : (
            <>
              {erro ? <DsAlert tone="error">{erro}</DsAlert> : null}
              {bloqueios.length > 0 ? (
                <DsAlert tone="warning" title="Confirmação bloqueada">
                  <ul className="list-disc space-y-1 pl-4">
                    {bloqueios.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </DsAlert>
              ) : null}

              <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Viagem
                  </dt>
                  <dd className="font-semibold">{viagem?.viagem_label ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Sentido
                  </dt>
                  <dd className="font-semibold capitalize">
                    {viagem?.sentido ?? '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Mapa
                  </dt>
                  <dd className="font-semibold">{viagem?.mapa ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Turno
                  </dt>
                  <dd className="font-semibold">
                    {viagem?.turno || guia?.turno_descricao || '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Empresa
                  </dt>
                  <dd className="font-semibold">{empresa}</dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Linha
                  </dt>
                  <dd className="font-semibold">{linha}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Carro
                  </dt>
                  <dd className="font-semibold tabular-nums">{carro}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Motorista (escala)
                  </dt>
                  <dd className="font-semibold">
                    {motoristaLabel || (
                      <span className="text-destructive">Não vinculado</span>
                    )}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Despachante responsável
                  </dt>
                  <dd className="font-semibold">{despachante}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                    Data/hora atual
                  </dt>
                  <dd className="text-muted-foreground">{agoraLabel()}</dd>
                </div>
              </dl>

              <FormField
                label="Saída real (HH:MM)"
                name="hor_saida_real"
                type="time"
                value={horSaida}
                onChange={(e) => setHorSaida(e.target.value)}
                hint="Horário real de saída — não use o previsto da escala automaticamente."
              />
            </>
          )}
        </div>

        <DialogFooter className="gap-2 border-t border-field px-5 py-4 sm:flex-col">
          {guia && viagem && (guia.id_item_map || viagem.id_item_map) ? (
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={submitting || loading}
              onClick={() => onTrocaMotorista(guia, viagem)}
            >
              Trocar motorista (com justificativa)
            </Button>
          ) : null}
          <Button
            ref={confirmRef}
            type="button"
            className="ds-cta w-full"
            disabled={!podeConfirmar || submitting || loading}
            onClick={() => void confirmar()}
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Confirmando…
              </>
            ) : (
              'Confirmar saída'
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            disabled={submitting}
            onClick={() => handleOpenChange(false)}
          >
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
