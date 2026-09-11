import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  formatLinhaLabel,
  formatLocalLabel,
  getEntradaSaidaContexto,
  getLinhasSaidaReferencia,
  registrarEntradaSaida,
  type LinhaEntradaSaida,
  type LocalEntradaSaida,
} from '@/api/entradaSaida';
import { ApiRequestError } from '@/api/client';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useScreenBg } from '@/hooks/useScreenBg';
import { cn } from '@/lib/utils';
import { onlyDigits } from '@/utils/validation';
import { SCREEN_BG } from '@/theme/tokens';

const BG = SCREEN_BG;
const LINHA_ITEM_H_PX = 44;
const LINHA_LIST_MAX_VISIBLE = 3;
const LINHA_LIST_MAX_H = LINHA_ITEM_H_PX * LINHA_LIST_MAX_VISIBLE;

const compactFieldClass =
  'h-10 rounded-lg bg-white text-sm shadow-none border-slate-400';
const halfFieldClass = cn(compactFieldClass, 'max-w-[50%]');
const compactLabelClass =
  'flex h-4 items-center text-[13px] font-semibold uppercase leading-none text-slate-900';
const linhaListLabelClass =
  'flex h-4 items-center text-xs font-semibold uppercase leading-none text-slate-900';

function maskHHMM(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

function isValidHHMM(value: string): boolean {
  if (!/^\d{2}:\d{2}$/.test(value)) return false;
  const h = Number(value.slice(0, 2));
  const m = Number(value.slice(3, 5));
  return h >= 0 && h <= 23 && m >= 0 && m <= 59;
}

function apiMsg(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) return err.body.mensagem || fallback;
  return fallback;
}

/** Telas 05/06 — Chegada | Saída (tb_chegada_saida; id_guia só no backend). */
export function EntradaSaidaScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);
  const entCarroRef = useRef<HTMLInputElement>(null);
  const saiCarroRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(true);
  const [linhas, setLinhas] = useState<LinhaEntradaSaida[]>([]);
  const [locais, setLocais] = useState<LocalEntradaSaida[]>([]);
  const [linhasSaida, setLinhasSaida] = useState<LinhaEntradaSaida[]>([]);
  const [idLinhaSel, setIdLinhaSel] = useState('');
  const [abaAtiva, setAbaAtiva] = useState<'chegada' | 'saida'>('chegada');
  const [semLocal, setSemLocal] = useState(false);

  const [entCarro, setEntCarro] = useState('');
  const [entHorario, setEntHorario] = useState('');
  const [entRoleta, setEntRoleta] = useState('');
  const [entTemperatura, setEntTemperatura] = useState('');
  const [saiCarro, setSaiCarro] = useState('');
  const [saiHorario, setSaiHorario] = useState('');
  const [saiLinha, setSaiLinha] = useState('');
  const [saiDestinoLabel, setSaiDestinoLabel] = useState('');
  const [saiTemperatura, setSaiTemperatura] = useState('');

  const [busy, setBusy] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const linhaSelecionada = useMemo(
    () => linhas.find((l) => String(l.id_linha) === idLinhaSel) ?? null,
    [idLinhaSel, linhas],
  );

  const semLinhas = !loading && (semLocal || linhas.length === 0);

  const limparCamposChegada = useCallback(() => {
    setEntCarro('');
    setEntHorario('');
    setEntRoleta('');
    setEntTemperatura('');
  }, []);

  const limparCamposSaida = useCallback(() => {
    setSaiCarro('');
    setSaiHorario('');
    setSaiLinha('');
    setSaiTemperatura('');
  }, []);

  const limparTodasAbas = useCallback(() => {
    limparCamposChegada();
    limparCamposSaida();
    setAbaAtiva('chegada');
  }, [limparCamposChegada, limparCamposSaida]);

  const focarCarroAba = useCallback((aba: 'chegada' | 'saida') => {
    window.setTimeout(() => {
      if (aba === 'chegada') entCarroRef.current?.focus();
      else saiCarroRef.current?.focus();
    }, 0);
  }, []);

  const handleAbaChange = useCallback(
    (value: string) => {
      const aba = value === 'saida' ? 'saida' : 'chegada';
      setAbaAtiva(aba);
      if (aba === 'chegada') limparCamposChegada();
      else limparCamposSaida();
      focarCarroAba(aba);
    },
    [focarCarroAba, limparCamposChegada, limparCamposSaida],
  );

  const selecionarLinha = useCallback(
    (id: string) => {
      setIdLinhaSel(id);
      limparTodasAbas();
      focarCarroAba('chegada');
    },
    [focarCarroAba, limparTodasAbas],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getEntradaSaidaContexto();
        if (cancelled) return;
        setLinhas(data.linhas ?? []);
        setLocais(data.locais ?? []);
        setSemLocal(data.id_local_usuario == null);
      } catch {
        if (!cancelled) navigate('/principal', { replace: true });
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  useEffect(() => {
    if (!idLinhaSel) {
      setLinhasSaida([]);
      setSaiDestinoLabel('');
      return;
    }

    const linha = linhas.find((l) => String(l.id_linha) === idLinhaSel);
    if (linha?.id_local_destino != null) {
      const local = locais.find((l) => l.id_local === linha.id_local_destino);
      setSaiDestinoLabel(local ? formatLocalLabel(local) : '');
    } else {
      setSaiDestinoLabel('');
    }

    void (async () => {
      const id = Number(idLinhaSel);
      if (!Number.isFinite(id)) return;
      try {
        const data = await getLinhasSaidaReferencia(id);
        setLinhasSaida(data.linhas ?? []);
      } catch {
        setLinhasSaida([]);
      }
    })();
  }, [idLinhaSel, linhas, locais]);

  const confirmar = async () => {
    if (busy || !idLinhaSel || !linhaSelecionada) {
      if (!idLinhaSel) setInfoMsg('Selecione uma linha.');
      return;
    }

    const isChegada = abaAtiva === 'chegada';
    const carro = (isChegada ? entCarro : saiCarro).trim();
    const horario = (isChegada ? entHorario : saiHorario).trim();
    const temperatura = (isChegada ? entTemperatura : saiTemperatura).trim();

    if (!carro || !/^\d{1,5}$/.test(carro)) {
      setInfoMsg('Informe o carro (até 5 dígitos).');
      return;
    }
    if (!isValidHHMM(horario)) {
      setInfoMsg('Informe o horário no formato HH:MM.');
      return;
    }

    // id_guia NÃO é enviado — o backend resolve por carro/data/hor_fim nulo.
    setBusy(true);
    try {
      await registrarEntradaSaida({
        evento: isChegada ? 'C' : 'S',
        id_linha: Number(idLinhaSel),
        carro,
        horario,
        ...(temperatura ? { temperatura } : {}),
        ...(isChegada && entRoleta.trim() ? { roleta: entRoleta.trim() } : {}),
        ...(!isChegada && saiLinha
          ? { id_linha_destino: Number(saiLinha) }
          : {}),
        ...(!isChegada && linhaSelecionada.id_local_destino != null
          ? { id_destino: linhaSelecionada.id_local_destino }
          : {}),
      });
      navigate('/registros');
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível registrar chegada/saída.'));
    } finally {
      setBusy(false);
    }
  };

  const cancelar = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate('/registros');
  };

  if (loading) {
    return (
      <AppShell className="bg-screen">
        <div className="page min-h-dvh bg-screen">
          <PageHeader title="CHEGADA | SAÍDA" onBack={cancelar} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  if (semLinhas) {
    return (
      <AppShell className="bg-screen">
        <div className="page flex min-h-dvh flex-col bg-screen">
          <PageHeader title="CHEGADA | SAÍDA" onBack={cancelar} />
          <EmptyState
            title={semLocal ? 'Usuário sem local' : 'Nenhuma linha'}
            description={
              semLocal
                ? 'Seu usuário não possui local cadastrado. Não há linhas para exibir.'
                : 'Não há linhas ativas vinculadas ao seu local.'
            }
            action={
              <Button type="button" variant="outline" onClick={cancelar}>
                Voltar
              </Button>
            }
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="CHEGADA | SAÍDA" onBack={cancelar} />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-3">
          <div className="flex w-full shrink-0 flex-col gap-1.5">
            <Label className={linhaListLabelClass}>Linha(s):</Label>
            <div
              className="overflow-y-auto rounded-lg border border-slate-400 bg-white"
              style={{ maxHeight: LINHA_LIST_MAX_H }}
              role="listbox"
              aria-label="Linhas disponíveis"
            >
              {linhas.map((l) => {
                const selected = String(l.id_linha) === idLinhaSel;
                return (
                  <button
                    key={l.id_linha}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={cn(
                      'flex min-h-[44px] w-full items-center border-b border-slate-200 px-3 text-left text-[15px] last:border-b-0',
                      selected
                        ? 'bg-primary/15 font-semibold text-slate-900'
                        : 'bg-white text-slate-800 active:bg-slate-100',
                    )}
                    onClick={() => selecionarLinha(String(l.id_linha))}
                  >
                    {formatLinhaLabel(l)}
                  </button>
                );
              })}
            </div>
          </div>

          {linhaSelecionada ? (
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border-2 border-slate-500/40 bg-white/50 p-2">
              <Tabs
                value={abaAtiva}
                onValueChange={handleAbaChange}
                className="flex min-h-0 flex-1 flex-col"
              >
                <TabsList className="h-10 shrink-0">
                  <TabsTrigger value="chegada" className="text-xs">
                    Chegada
                  </TabsTrigger>
                  <TabsTrigger value="saida" className="text-xs">
                    Saída
                  </TabsTrigger>
                </TabsList>

                <TabsContent
                  value="chegada"
                  className="mt-2 min-h-0 flex-1 overflow-y-auto field-stack gap-2"
                >
                  <FormField
                    ref={entCarroRef}
                    label="Carro"
                    name="ent_carro"
                    type="tel"
                    inputMode="numeric"
                    maxLength={5}
                    value={entCarro}
                    onChange={(e) => setEntCarro(onlyDigits(e.target.value, 5))}
                    className={halfFieldClass}
                  />
                  <FormField
                    label="Chegada"
                    name="ent_horario"
                    placeholder="HH:MM"
                    value={entHorario}
                    onChange={(e) => setEntHorario(maskHHMM(e.target.value))}
                    inputMode="numeric"
                    className={halfFieldClass}
                  />
                  <FormField
                    label="Roleta"
                    name="ent_roleta"
                    type="tel"
                    inputMode="numeric"
                    value={entRoleta}
                    onChange={(e) => setEntRoleta(onlyDigits(e.target.value))}
                    className={halfFieldClass}
                  />
                  <FormField
                    label="Temperatura"
                    name="ent_temperatura"
                    type="tel"
                    inputMode="numeric"
                    maxLength={2}
                    value={entTemperatura}
                    onChange={(e) =>
                      setEntTemperatura(onlyDigits(e.target.value).slice(0, 2))
                    }
                    className={halfFieldClass}
                  />
                </TabsContent>

                <TabsContent
                  value="saida"
                  className="mt-2 min-h-0 flex-1 overflow-y-auto field-stack gap-2"
                >
                  <FormField
                    ref={saiCarroRef}
                    label="Carro"
                    name="sai_carro"
                    type="tel"
                    inputMode="numeric"
                    maxLength={5}
                    value={saiCarro}
                    onChange={(e) => setSaiCarro(onlyDigits(e.target.value, 5))}
                    className={halfFieldClass}
                  />
                  <FormField
                    label="Saída"
                    name="sai_horario"
                    placeholder="HH:MM"
                    value={saiHorario}
                    onChange={(e) => setSaiHorario(maskHHMM(e.target.value))}
                    inputMode="numeric"
                    className={halfFieldClass}
                  />
                  <FormField
                    label="Temperatura"
                    name="sai_temperatura"
                    type="tel"
                    inputMode="numeric"
                    maxLength={2}
                    value={saiTemperatura}
                    onChange={(e) =>
                      setSaiTemperatura(onlyDigits(e.target.value).slice(0, 2))
                    }
                    className={halfFieldClass}
                  />

                  <div className="flex w-full flex-col gap-1">
                    <Label className={compactLabelClass}>Linha</Label>
                    <Select
                      value={saiLinha || undefined}
                      onValueChange={setSaiLinha}
                    >
                      <SelectTrigger
                        className={cn(compactFieldClass, 'h-10 w-full text-sm')}
                      >
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent className="max-h-[220px]">
                        {linhasSaida.map((l) => (
                          <SelectItem key={l.id_linha} value={String(l.id_linha)}>
                            {formatLinhaLabel(l)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <FormField
                    label="Destino"
                    name="sai_destino"
                    value={saiDestinoLabel}
                    readOnly
                    className={cn(compactFieldClass, 'w-full')}
                  />
                </TabsContent>
              </Tabs>
            </div>
          ) : (
            <p className="text-center text-sm text-muted-foreground">
              Selecione uma linha para registrar chegada ou saída.
            </p>
          )}

          <div className="mt-auto grid grid-cols-2 gap-3 border-t border-slate-400/40 pt-4">
            <Button
              type="button"
              className="h-12 text-base font-bold uppercase"
              onClick={() => void confirmar()}
              disabled={busy || !linhaSelecionada}
            >
              {busy ? 'Salvando…' : 'Confirmar'}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="h-12 border-slate-500 bg-white text-base font-bold uppercase"
              onClick={cancelar}
              disabled={busy}
            >
              Cancelar
            </Button>
          </div>
        </div>

        <AlertDialog
          open={infoMsg !== null}
          message={infoMsg ?? ''}
          onConfirm={() => setInfoMsg(null)}
        />
      </div>
    </AppShell>
  );
}
