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
import { AppDialog } from '@/components/shared/AppDialog';
import { FormField } from '@/components/forms/FormField';
import { PageHeader } from '@/components/shared/PageHeader';
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

const BG = '#B9C8D4';
/** Altura visível da lista de linhas (até 3 itens). */
const LINHA_ITEM_H_PX = 44;
const LINHA_LIST_MAX_VISIBLE = 3;
const LINHA_LIST_MAX_H = LINHA_ITEM_H_PX * LINHA_LIST_MAX_VISIBLE;

const compactFieldClass =
  'h-10 rounded-lg bg-white text-sm shadow-none border-slate-400';
/** Metade da largura da caixa Carro (full → 50%). */
const halfFieldClass = cn(compactFieldClass, 'max-w-[50%]');
const compactLabelClass =
  'flex h-4 items-center text-[13px] font-semibold uppercase leading-none text-slate-900';
const linhaListLabelClass =
  'flex h-4 items-center text-xs font-semibold uppercase leading-none text-slate-900';
const fullFieldClass = cn(compactFieldClass, 'w-full');

function maskHHMM(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

/** Tela Chegada | Saída — RF-57..RF-59 (tb_chegada_saida). */
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
  const [abaAtiva, setAbaAtiva] = useState('chegada');
  const [semLocal, setSemLocal] = useState(false);

  const [entCarro, setEntCarro] = useState('');
  const [entHorario, setEntHorario] = useState('');
  const [entRoleta, setEntRoleta] = useState('');
  const [entTemperatura, setEntTemperatura] = useState('');
  const [saiCarro, setSaiCarro] = useState('');
  const [saiHorario, setSaiHorario] = useState('');
  const [saiLinha, setSaiLinha] = useState('');
  const [saiDestino, setSaiDestino] = useState('');
  const [saiTemperatura, setSaiTemperatura] = useState('');

  const [busy, setBusy] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const linhaSelecionada = useMemo(
    () => linhas.find((l) => String(l.id_linha) === idLinhaSel) ?? null,
    [idLinhaSel, linhas],
  );

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
    setSaiDestino('');
    setSaiTemperatura('');
  }, []);

  /** RF-57b — limpa ambas as abas ao trocar de linha. */
  const limparTodasAbas = useCallback(() => {
    limparCamposChegada();
    limparCamposSaida();
    setAbaAtiva('chegada');
  }, [limparCamposChegada, limparCamposSaida]);

  const focarCarroAba = useCallback((aba: string) => {
    window.setTimeout(() => {
      if (aba === 'chegada') entCarroRef.current?.focus();
      else saiCarroRef.current?.focus();
    }, 0);
  }, []);

  /** RF-57 — ao trocar aba, limpa só a guia selecionada e foca o carro. */
  const handleAbaChange = useCallback(
    (value: string) => {
      setAbaAtiva(value);
      if (value === 'chegada') limparCamposChegada();
      else limparCamposSaida();
      focarCarroAba(value);
    },
    [focarCarroAba, limparCamposChegada, limparCamposSaida],
  );

  const carregarContexto = useCallback(async () => {
    setLoading(true);
    try {
      const { response, data } = await getEntradaSaidaContexto();
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        navigate('/principal', { replace: true });
        return;
      }
      setLinhas(data.linhas ?? []);
      setLocais(data.locais ?? []);
      setSemLocal(data.id_local_usuario == null);
    } catch {
      navigate('/principal', { replace: true });
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    void carregarContexto();
  }, [carregarContexto]);

  useEffect(() => {
    if (!idLinhaSel) {
      limparTodasAbas();
      setLinhasSaida([]);
      return;
    }

    limparTodasAbas();

    const linha = linhas.find((l) => String(l.id_linha) === idLinhaSel);
    if (linha?.id_local_destino != null) {
      const local = locais.find((l) => l.id_local === linha.id_local_destino);
      setSaiDestino(local ? formatLocalLabel(local) : '');
    }

    focarCarroAba('chegada');

    void (async () => {
      const id = Number(idLinhaSel);
      if (!Number.isFinite(id)) return;
      const { response, data } = await getLinhasSaidaReferencia(id);
      if (response.ok && data && 'ok' in data && data.ok === true) {
        setLinhasSaida(data.linhas ?? []);
      } else {
        setLinhasSaida([]);
      }
    })();
  }, [idLinhaSel, linhas, locais, limparTodasAbas, focarCarroAba]);

  const confirmar = async () => {
    if (busy || !idLinhaSel || !linhaSelecionada) {
      if (!idLinhaSel) setInfoMsg('Selecione uma linha.');
      return;
    }

    const isChegada = abaAtiva === 'chegada';
    const carro = isChegada ? entCarro.trim() : saiCarro.trim();
    const horario = isChegada ? entHorario.trim() : saiHorario.trim();
    const temperatura = isChegada ? entTemperatura.trim() : saiTemperatura.trim();

    if (!carro) {
      setInfoMsg('Informe o carro.');
      return;
    }
    if (!/^\d{2}:\d{2}$/.test(horario)) {
      setInfoMsg('Informe o horário no formato HH:MM.');
      return;
    }

    setBusy(true);
    try {
      const payload: Parameters<typeof registrarEntradaSaida>[0] = {
        evento: isChegada ? 'C' : 'S',
        id_linha: Number(idLinhaSel),
        carro,
        horario,
      };
      if (temperatura) payload.temperatura = temperatura;
      if (isChegada && entRoleta.trim()) payload.roleta = entRoleta.trim();
      if (!isChegada) {
        if (saiLinha) payload.id_linha_destino = Number(saiLinha);
        if (linhaSelecionada.id_local_destino != null) {
          payload.id_destino = linhaSelecionada.id_local_destino;
        }
      }

      const { response, data } = await registrarEntradaSaida(payload);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const msg =
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : 'Não foi possível registrar chegada/saída.';
        setInfoMsg(msg);
        return;
      }
      navigate('/principal');
    } catch {
      setInfoMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
        <PageHeader title="CHEGADA | SAÍDA" onBack={() => navigate('/principal')} />
        <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="page flex min-h-dvh flex-col bg-[#B9C8D4] text-slate-900">
      <PageHeader title="CHEGADA | SAÍDA" onBack={() => navigate('/principal')} />

      <div className="page-body flex min-h-0 flex-1 flex-col gap-3">
        <div className="flex w-full shrink-0 flex-col gap-1.5">
          <Label className={linhaListLabelClass}>
            Linha(s):
          </Label>
          {semLocal || linhas.length === 0 ? (
            <div className="flex h-12 items-center rounded-lg border border-slate-400 bg-white px-3 text-sm text-muted-foreground">
              {semLocal
                ? 'Usuário sem local cadastrado'
                : 'Nenhuma linha para seu local'}
            </div>
          ) : (
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
                    onClick={() => setIdLinhaSel(String(l.id_linha))}
                  >
                    {formatLinhaLabel(l)}
                  </button>
                );
              })}
            </div>
          )}
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
                  value={entCarro}
                  onChange={(e) => setEntCarro(e.target.value)}
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
                  onChange={(e) => setEntTemperatura(onlyDigits(e.target.value).slice(0, 2))}
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
                  value={saiCarro}
                  onChange={(e) => setSaiCarro(e.target.value)}
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
                  onChange={(e) => setSaiTemperatura(onlyDigits(e.target.value).slice(0, 2))}
                  className={halfFieldClass}
                />

                <div className="flex w-full flex-col gap-1">
                  <Label className={compactLabelClass}>Linha</Label>
                  <Select value={saiLinha || undefined} onValueChange={setSaiLinha}>
                    <SelectTrigger className={cn(compactFieldClass, 'h-10 w-full text-sm')}>
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
                  value={saiDestino}
                  onChange={(e) => setSaiDestino(e.target.value)}
                  className={fullFieldClass}
                />
              </TabsContent>
            </Tabs>
          </div>
        ) : null}

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
            onClick={() => navigate('/principal')}
            disabled={busy}
          >
            Cancelar
          </Button>
        </div>
      </div>

      <AppDialog
        open={infoMsg !== null}
        message={infoMsg ?? ''}
        confirmLabel="OK"
        onConfirm={() => setInfoMsg(null)}
      />
    </div>
  );
}
