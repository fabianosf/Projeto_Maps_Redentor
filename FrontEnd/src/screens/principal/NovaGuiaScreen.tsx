import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiRequestError } from '@/api/client';
import {
  createGuia,
  getContextoEscala,
  listEscalasGuia,
  registrarAlteracaoEscala,
} from '@/api/guia';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { FormField } from '@/components/FormField';
import { PageHeader } from '@/components/PageHeader';
import { DatePickerField } from '@/components/forms/DatePickerField';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { cn } from '@/lib/utils';
import type {
  GuiaContextoEscala,
  GuiaEscalaOpcao,
  GuiaMapaOpcao,
  GuiaPayload,
} from '@/types/guia';
import { SCREEN_BG } from '@/theme/tokens';
import { parseDateBR } from '@/utils/appFormat';
import { formatCodigoMapa } from '@/utils/mapaFormat';
import { canAccessMapas } from '@/utils/perfilAccess';
import { onlyDigits } from '@/utils/validation';

const BG = SCREEN_BG;
const MSG_CADASTRO_ERRO = 'Não foi possível cadastrar a guia!';
const OBS_MAX = 150;
const SELECT_EMPTY = '__empty__';

const fieldClass = 'h-10 rounded-lg bg-white text-sm shadow-none border-slate-400';
const halfFieldClass = cn(fieldClass, 'w-full max-w-none');
const selectTriggerClass = cn(fieldClass, 'h-10 w-full text-sm');
const labelClass =
  'flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900';

function toSelectValue(v: string): string {
  return v === '' ? SELECT_EMPTY : v;
}

function fromSelectValue(v: string): string {
  return v === SELECT_EMPTY ? '' : v;
}

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

function dataHojeBR(): string {
  const hoje = new Date();
  const dd = String(hoje.getDate()).padStart(2, '0');
  const mm = String(hoje.getMonth() + 1).padStart(2, '0');
  const yyyy = hoje.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function apiMsg(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) {
    return err.body.mensagem || fallback;
  }
  return fallback;
}

function ReadonlyField({
  label,
  value,
}: {
  label: string;
  value?: string | number | null;
}) {
  return (
    <div className="flex w-full flex-col gap-1">
      <span className={labelClass}>{label}</span>
      <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800">
        {value != null && String(value).trim() !== '' ? String(value) : '—'}
      </p>
    </div>
  );
}

function montarPayload(state: {
  dataGuia: string;
  idEmpresa: string;
  idLinha: string;
  idTurno: string;
  carro: string;
  motorista: string;
  horarioPegada: string;
  horarioLargada: string;
  roletaInicial: string;
  roletaFinal: string;
  roleta2Inicial: string;
  roleta2Final: string;
  observacao: string;
  idItemMap: string;
  pasIda: string;
  pasVolta: string;
  ocorrencias: string;
}): GuiaPayload {
  return {
    numero: '',
    data: state.dataGuia.trim(),
    id_empresa: state.idEmpresa ? Number(state.idEmpresa) : null,
    id_linha: state.idLinha ? Number(state.idLinha) : null,
    id_turno: state.idTurno ? Number(state.idTurno) : null,
    id_item_map: state.idItemMap ? Number(state.idItemMap) : null,
    carro: state.carro.trim(),
    motorista: state.motorista.trim(),
    horario_pegada: state.horarioPegada.trim(),
    horario_largada: state.horarioLargada.trim(),
    roleta01_inicial: state.roletaInicial ? Number(state.roletaInicial) : null,
    roleta01_final: state.roletaFinal ? Number(state.roletaFinal) : null,
    roleta2_inicial: state.roleta2Inicial ? Number(state.roleta2Inicial) : null,
    roleta2_final: state.roleta2Final ? Number(state.roleta2Final) : null,
    pas_ida: state.pasIda ? Number(state.pasIda) : null,
    pas_volta: state.pasVolta ? Number(state.pasVolta) : null,
    ocorrencias: state.ocorrencias.trim() || undefined,
    observacao: state.observacao.trim(),
  };
}

function validarFormulario(payload: GuiaPayload): string | null {
  if (!parseDateBR(payload.data.trim())) return 'Data inválida.';
  if (!payload.id_item_map) {
    return 'Selecione o mapa/turno e o carro/escala.';
  }
  const ini = payload.horario_pegada ?? '';
  const fim = payload.horario_largada ?? '';
  if (ini && !isValidHHMM(ini)) return 'INÍCIO(JORNADA) inválido.';
  if (fim && !isValidHHMM(fim)) return 'FIM(JORNADA) inválido.';
  if ((payload.observacao ?? '').length > OBS_MAX) {
    return `Observação deve ter no máximo ${OBS_MAX} caracteres.`;
  }
  return null;
}

/** Tela full-page — Nova guia a partir de Mapa/Escala. Rota: `/guia/nova`. */
export function NovaGuiaScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(BG);
  const aliveRef = useRef(true);

  const [busy, setBusy] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const [dataGuia, setDataGuia] = useState(dataHojeBR);
  const [idEmpresa, setIdEmpresa] = useState('');
  const [idLinha, setIdLinha] = useState('');
  const [idTurno, setIdTurno] = useState('');
  const [carro, setCarro] = useState('');
  const [motorista, setMotorista] = useState('');
  const [horarioPegada, setHorarioPegada] = useState('');
  const [horarioLargada, setHorarioLargada] = useState('');
  const [roletaInicial, setRoletaInicial] = useState('');
  const [roletaFinal, setRoletaFinal] = useState('');
  const [roleta2Inicial, setRoleta2Inicial] = useState('');
  const [roleta2Final, setRoleta2Final] = useState('');
  const [observacao, setObservacao] = useState('');
  const [idItemMap, setIdItemMap] = useState('');
  const [pasIda, setPasIda] = useState('');
  const [pasVolta, setPasVolta] = useState('');
  const [ocorrencias, setOcorrencias] = useState('');

  const [mapasOpcoes, setMapasOpcoes] = useState<GuiaMapaOpcao[]>([]);
  const [escalasOpcoes, setEscalasOpcoes] = useState<GuiaEscalaOpcao[]>([]);
  const [idMapaSel, setIdMapaSel] = useState('');
  const [contextoEscala, setContextoEscala] = useState<GuiaContextoEscala | null>(
    null,
  );
  const [escalasLoading, setEscalasLoading] = useState(false);

  const [alteracaoOpen, setAlteracaoOpen] = useState(false);
  const [altCarro, setAltCarro] = useState('');
  const [altMotorista, setAltMotorista] = useState('');
  const [altHorIni, setAltHorIni] = useState('');
  const [altHorFim, setAltHorFim] = useState('');
  const [altChegada, setAltChegada] = useState('');
  const [altJustificativa, setAltJustificativa] = useState('');

  const podeAlterarEscala = canAccessMapas(user?.codigo_perfil);
  const camposHabilitados = !busy;

  const carregarEscalasDoDia = async (dataBr: string, idMapa?: number) => {
    if (!parseDateBR(dataBr)) {
      setMapasOpcoes([]);
      setEscalasOpcoes([]);
      return;
    }
    setEscalasLoading(true);
    try {
      const data = await listEscalasGuia({
        data: dataBr,
        id_mapa: idMapa,
      });
      if (!aliveRef.current) return;
      setMapasOpcoes(data.mapas ?? []);
      setEscalasOpcoes(idMapa != null ? (data.escalas ?? []) : []);
    } catch (err) {
      if (!aliveRef.current) return;
      setMapasOpcoes([]);
      setEscalasOpcoes([]);
      setInfoMsg(apiMsg(err, 'Não foi possível carregar escalas do dia.'));
    } finally {
      if (aliveRef.current) setEscalasLoading(false);
    }
  };

  useEffect(() => {
    aliveRef.current = true;
    void carregarEscalasDoDia(dataGuia);
    return () => {
      aliveRef.current = false;
    };
    // Carga inicial com a data padrão do dia
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const aplicarContextoNoForm = (ctx: GuiaContextoEscala) => {
    setContextoEscala(ctx);
    setIdItemMap(String(ctx.id_item));
    setIdEmpresa(ctx.id_empresa != null ? String(ctx.id_empresa) : '');
    setIdLinha(ctx.id_linha != null ? String(ctx.id_linha) : '');
    setIdTurno(ctx.id_turno != null ? String(ctx.id_turno) : '');
    setCarro(ctx.numero_frota ? String(ctx.numero_frota) : '');
    setMotorista(ctx.matricula_motorista ? String(ctx.matricula_motorista) : '');
    if (ctx.data) setDataGuia(ctx.data);
  };

  const selecionarEscala = async (idItemStr: string) => {
    if (!idItemStr) {
      setIdItemMap('');
      setContextoEscala(null);
      return;
    }
    setBusy(true);
    try {
      const data = await getContextoEscala(Number(idItemStr));
      aplicarContextoNoForm(data.contexto);
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível carregar a escala.'));
      setContextoEscala(null);
      setIdItemMap('');
    } finally {
      setBusy(false);
    }
  };

  const salvar = async () => {
    if (busy) return;
    const body = montarPayload({
      dataGuia,
      idEmpresa,
      idLinha,
      idTurno,
      carro,
      motorista,
      horarioPegada,
      horarioLargada,
      roletaInicial,
      roletaFinal,
      roleta2Inicial,
      roleta2Final,
      observacao,
      idItemMap,
      pasIda,
      pasVolta,
      ocorrencias,
    });
    const erroLocal = validarFormulario(body);
    if (erroLocal) {
      setInfoMsg(erroLocal);
      return;
    }

    setBusy(true);
    try {
      await createGuia(body);
      navigate('/guia');
    } catch (err) {
      setInfoMsg(apiMsg(err, MSG_CADASTRO_ERRO));
    } finally {
      setBusy(false);
    }
  };

  const confirmarAlteracaoEscala = async () => {
    if (!idItemMap || busy) return;
    const just = altJustificativa.trim();
    if (!just) {
      setInfoMsg('Informe a justificativa da alteração de escala.');
      return;
    }
    setBusy(true);
    try {
      const data = await registrarAlteracaoEscala(Number(idItemMap), {
        justificativa: just,
        numero_frota: altCarro.trim() || undefined,
        matricula_motorista: altMotorista.trim() || undefined,
        hor_ini_jor: altHorIni.trim() || undefined,
        hor_fim_jor: altHorFim.trim() || undefined,
        chegada_ponto: altChegada.trim() || undefined,
      });
      aplicarContextoNoForm(data.contexto);
      setAlteracaoOpen(false);
      setAltJustificativa('');
      setInfoMsg(data.mensagem ?? 'Alteração de escala registrada com auditoria.');
      if (dataGuia) {
        void carregarEscalasDoDia(
          dataGuia,
          idMapaSel ? Number(idMapaSel) : undefined,
        );
      }
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível alterar a escala.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="Nova guia" onBack={() => navigate('/guia')} />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-4">
          <ReadonlyField
            label="NR(Guia)"
            value="Gerado automaticamente ao salvar"
          />

          <DatePickerField
            label="Data"
            name="data_guia"
            value={dataGuia}
            onChange={(v) => {
              setDataGuia(v);
              setIdMapaSel('');
              setIdItemMap('');
              setContextoEscala(null);
              setEscalasOpcoes([]);
              void carregarEscalasDoDia(v);
            }}
            iconBesideLabel
            inputClassName="h-10 text-sm shadow-none"
            disabled={!camposHabilitados}
          />

          <div className="flex w-full flex-col gap-1.5">
            <Label className={labelClass}>Mapa / Turno</Label>
            <Select
              value={toSelectValue(idMapaSel)}
              onValueChange={(v) => {
                const id = fromSelectValue(v);
                setIdMapaSel(id);
                setIdItemMap('');
                setContextoEscala(null);
                setEscalasOpcoes([]);
                if (id) {
                  void carregarEscalasDoDia(dataGuia, Number(id));
                }
              }}
              disabled={!camposHabilitados || escalasLoading}
            >
              <SelectTrigger
                className={selectTriggerClass}
                aria-label="Mapa / Turno"
              >
                <SelectValue
                  placeholder={
                    escalasLoading ? 'Carregando…' : 'Selecione o mapa'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                  Selecione
                </SelectItem>
                {mapasOpcoes.map((m) => (
                  <SelectItem key={m.id_registro} value={String(m.id_registro)}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex w-full flex-col gap-1.5">
            <Label className={labelClass}>Carro / Escala</Label>
            <Select
              value={toSelectValue(idItemMap)}
              onValueChange={(v) => void selecionarEscala(fromSelectValue(v))}
              disabled={!camposHabilitados || !idMapaSel || escalasLoading}
            >
              <SelectTrigger
                className={selectTriggerClass}
                aria-label="Carro / Escala"
              >
                <SelectValue
                  placeholder={
                    !idMapaSel
                      ? 'Selecione o mapa primeiro'
                      : escalasOpcoes.length === 0
                        ? 'Nenhum carro neste mapa'
                        : 'Selecione o carro/escala'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                  Selecione
                </SelectItem>
                {escalasOpcoes.map((e) => (
                  <SelectItem key={e.id_item} value={String(e.id_item)}>
                    {e.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {contextoEscala ? (
            <div className="space-y-3 rounded-xl border border-slate-300 bg-white/70 p-3">
              <p className="text-center text-[13px] font-semibold uppercase tracking-wide text-slate-700">
                Dados da escala (somente leitura)
              </p>
              <div className="grid grid-cols-2 gap-2">
                <ReadonlyField
                  label="Mapa"
                  value={formatCodigoMapa(contextoEscala.codigo_mapa)}
                />
                <ReadonlyField label="Empresa" value={contextoEscala.empresa} />
                <ReadonlyField
                  label="Linha"
                  value={
                    contextoEscala.codigo_linha != null
                      ? `${contextoEscala.codigo_linha}${
                          contextoEscala.linha
                            ? `-${contextoEscala.linha}`
                            : ''
                        }`
                      : contextoEscala.linha
                  }
                />
                <ReadonlyField label="Turno" value={contextoEscala.turno} />
                <ReadonlyField
                  label="Veículo"
                  value={contextoEscala.numero_frota}
                />
                <ReadonlyField
                  label="Motorista"
                  value={
                    contextoEscala.matricula_motorista
                      ? `${contextoEscala.matricula_motorista}${
                          contextoEscala.motorista
                            ? ` — ${contextoEscala.motorista}`
                            : ''
                        }`
                      : contextoEscala.motorista
                  }
                />
                <ReadonlyField
                  label="Chegada ao ponto"
                  value={contextoEscala.chegada_ponto_hhmm}
                />
                <ReadonlyField
                  label="Início previsto"
                  value={contextoEscala.hor_ini_jor_hhmm}
                />
                <ReadonlyField
                  label="Fim previsto"
                  value={contextoEscala.hor_fim_jor_hhmm}
                />
              </div>
              {(contextoEscala.viagens_previstas?.length ?? 0) > 0 ? (
                <div>
                  <p className={`${labelClass} mb-1`}>Viagens previstas</p>
                  <ul className="max-h-28 space-y-1 overflow-y-auto text-sm text-slate-700">
                    {contextoEscala.viagens_previstas!.map((v, idx) => (
                      <li
                        key={v.id_viagem ?? idx}
                        className="rounded border border-slate-200 bg-slate-50 px-2 py-1"
                      >
                        {v.horario_saida ?? '—'} → {v.horario_chegada ?? '—'}
                        {v.qtd_pas_ida != null || v.qtd_pas_volta != null
                          ? ` · IDA ${v.qtd_pas_ida ?? '—'} / VOLTA ${v.qtd_pas_volta ?? '—'}`
                          : null}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {podeAlterarEscala && idItemMap ? (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  disabled={busy}
                  onClick={() => {
                    setAltCarro(contextoEscala.numero_frota ?? '');
                    setAltMotorista(contextoEscala.matricula_motorista ?? '');
                    setAltHorIni(contextoEscala.hor_ini_jor_hhmm ?? '');
                    setAltHorFim(contextoEscala.hor_fim_jor_hhmm ?? '');
                    setAltChegada(contextoEscala.chegada_ponto_hhmm ?? '');
                    setAltJustificativa('');
                    setAlteracaoOpen(true);
                  }}
                >
                  Registrar alteração de escala
                </Button>
              ) : null}
            </div>
          ) : null}

          <p className="pt-1 text-center text-[13px] font-semibold uppercase tracking-wide text-slate-700">
            Dados da execução
          </p>

          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Início(Jornada)"
              name="hor_ini"
              type="text"
              inputMode="numeric"
              placeholder="HH:MM real"
              value={horarioPegada}
              onChange={(e) => setHorarioPegada(maskHHMM(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
            <FormField
              label="Fim(Jornada)"
              name="hor_fim"
              type="text"
              inputMode="numeric"
              placeholder="HH:MM real"
              value={horarioLargada}
              onChange={(e) => setHorarioLargada(maskHHMM(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Viagens IDA"
              name="pas_ida"
              type="tel"
              inputMode="numeric"
              value={pasIda}
              onChange={(e) => setPasIda(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
            <FormField
              label="Viagens VOLTA"
              name="pas_volta"
              type="tel"
              inputMode="numeric"
              value={pasVolta}
              onChange={(e) => setPasVolta(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Ja E inicial"
              name="roleta01_ini"
              type="tel"
              inputMode="numeric"
              value={roletaInicial}
              onChange={(e) => setRoletaInicial(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
            <FormField
              label="Ja E final"
              name="roleta01_fim"
              type="tel"
              inputMode="numeric"
              value={roletaFinal}
              onChange={(e) => setRoletaFinal(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="RioCard inicial"
              name="roleta2_ini"
              type="tel"
              inputMode="numeric"
              value={roleta2Inicial}
              onChange={(e) => setRoleta2Inicial(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
            <FormField
              label="RioCard final"
              name="roleta2_fim"
              type="tel"
              inputMode="numeric"
              value={roleta2Final}
              onChange={(e) => setRoleta2Final(onlyDigits(e.target.value))}
              className={halfFieldClass}
              disabled={!camposHabilitados}
            />
          </div>

          <div className="flex w-full flex-col gap-1.5">
            <Label className={labelClass} htmlFor="ocorrencias_nova_guia">
              Ocorrências
            </Label>
            <textarea
              id="ocorrencias_nova_guia"
              name="ocorrencias"
              rows={2}
              maxLength={80}
              value={ocorrencias}
              onChange={(e) => setOcorrencias(e.target.value.slice(0, 80))}
              disabled={!camposHabilitados}
              className={cn(
                fieldClass,
                'min-h-[3.5rem] w-full resize-y px-3 py-2 text-sm disabled:opacity-60',
              )}
            />
          </div>

          <div className="flex w-full flex-col gap-1.5">
            <Label className={labelClass} htmlFor="observacao_nova_guia">
              Observações
            </Label>
            <textarea
              id="observacao_nova_guia"
              name="observacao"
              rows={3}
              maxLength={OBS_MAX}
              value={observacao}
              onChange={(e) => setObservacao(e.target.value.slice(0, OBS_MAX))}
              disabled={!camposHabilitados}
              className={cn(
                fieldClass,
                'min-h-[4.5rem] w-full resize-y px-3 py-2 text-sm disabled:opacity-60',
              )}
            />
          </div>

          <div className="mt-auto flex gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              disabled={busy}
              onClick={() => navigate('/guia')}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              className="flex-1"
              disabled={busy}
              onClick={() => void salvar()}
            >
              Salvar
            </Button>
          </div>
        </div>

        <AlertDialog
          open={infoMsg != null}
          message={infoMsg ?? ''}
          onConfirm={() => setInfoMsg(null)}
        />

        <Dialog open={alteracaoOpen} onOpenChange={setAlteracaoOpen}>
          <DialogContent className="max-w-[380px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Alteração de escala
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              Troca de veículo, motorista ou horário exige justificativa e fica
              registrada na auditoria.
            </p>
            <div className="mt-3 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  label="Carro"
                  name="alt_carro"
                  type="tel"
                  inputMode="numeric"
                  maxLength={5}
                  value={altCarro}
                  onChange={(e) => setAltCarro(onlyDigits(e.target.value, 5))}
                  className={halfFieldClass}
                />
                <FormField
                  label="Motorista"
                  name="alt_motorista"
                  type="tel"
                  inputMode="numeric"
                  maxLength={5}
                  value={altMotorista}
                  onChange={(e) =>
                    setAltMotorista(onlyDigits(e.target.value, 5))
                  }
                  className={halfFieldClass}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  label="Início previsto"
                  name="alt_hor_ini"
                  type="text"
                  inputMode="numeric"
                  placeholder="HH:MM"
                  value={altHorIni}
                  onChange={(e) => setAltHorIni(maskHHMM(e.target.value))}
                  className={halfFieldClass}
                />
                <FormField
                  label="Fim previsto"
                  name="alt_hor_fim"
                  type="text"
                  inputMode="numeric"
                  placeholder="HH:MM"
                  value={altHorFim}
                  onChange={(e) => setAltHorFim(maskHHMM(e.target.value))}
                  className={halfFieldClass}
                />
              </div>
              <FormField
                label="Chegada ao ponto"
                name="alt_chegada"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                value={altChegada}
                onChange={(e) => setAltChegada(maskHHMM(e.target.value))}
                className={fieldClass}
              />
              <div>
                <Label
                  htmlFor="justificativa_escala_nova"
                  className="mb-1.5 block text-sm font-semibold"
                >
                  Justificativa
                </Label>
                <textarea
                  id="justificativa_escala_nova"
                  rows={3}
                  maxLength={300}
                  value={altJustificativa}
                  onChange={(e) => setAltJustificativa(e.target.value)}
                  className={cn(
                    fieldClass,
                    'min-h-[4rem] w-full resize-y px-3 py-2',
                  )}
                />
              </div>
            </div>
            <DialogFooter className="mt-4 gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setAlteracaoOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy || !altJustificativa.trim()}
                onClick={() => void confirmarAlteracaoEscala()}
              >
                Confirmar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
