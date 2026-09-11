import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bus,
  CalendarDays,
  Clock3,
  Plus,
  Search,
} from 'lucide-react';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import {
  createGuia,
  deleteGuia,
  encerrarGuia,
  getContextoEscala,
  getGuia,
  getGuiaByNumero,
  getHistoricoRoleta,
  iniciarTrechoGuia,
  concluirTrechoGuia,
  cancelarTrechoGuia,
  criarTrechoGuia,
  atualizarTrechoGuia,
  listEscalasGuia,
  listGuias,
  registrarAjusteManual,
  registrarAlteracaoEscala,
  registrarAlteracaoGuia,
  salvarRoletaLeitura,
  updateGuia,
} from '@/api/guia';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { FormField } from '@/components/FormField';
import { RegistrarSaidaPanel } from '@/components/guia/RegistrarSaidaPanel';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import {
  AlertPanel,
  FilterChipsBar,
  OpsCard,
  PrimaryActionButton,
  StatusSeal,
} from '@/components/ops';
import { DatePickerField } from '@/components/forms/DatePickerField';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
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
import type { CadastrosMestres, LinhaCadastro } from '@/types/cadastro';
import type {
  Guia,
  GuiaAlteracao,
  GuiaContextoEscala,
  GuiaEscalaOpcao,
  GuiaFonteRoleta,
  GuiaMapaOpcao,
  GuiaPayload,
  GuiaResumoDia,
  GuiaRoletaBloco,
  GuiaRoletaHistoricoItem,
  GuiaSyncStatus,
  GuiaTrecho,
  GuiaViagemCard,
  OrigemEmbarque,
  SentidoViagem,
} from '@/types/guia';
import { SCREEN_BG } from '@/theme/tokens';
import { parseDateBR, toDateBR } from '@/utils/appFormat';
import {
  agruparViagensOperacionais,
  contarPendentesOperacionais,
  formatDataChip,
  labelProximaAcao,
  labelStatusGuia,
  labelStatusOperacional,
  statusOperacionalViagem,
  stripeClassStatusOperacional,
  type ProximaAcaoTipo,
} from '@/utils/guiaView';
import { canAccessMapas } from '@/utils/perfilAccess';
import { onlyDigits } from '@/utils/validation';

const BG = SCREEN_BG;
const MSG_CADASTRO_OK = 'Guia cadastrada com sucesso!';
const MSG_CADASTRO_ERRO = 'Não foi possível cadastrar a guia!';
const MSG_EXCLUSAO_OK = 'Guia excluída com sucesso!';
const OBS_MAX = 150;
const NR_MAX = 15;
const SELECT_EMPTY = '__empty__';

type GuiaModo = 'idle' | 'include' | 'edit';
type FiltroSentido = 'todos' | SentidoViagem;
type FiltroOrigem = 'todos' | OrigemEmbarque;

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

function formatLinhaLabel(l: LinhaCadastro): string {
  const cod =
    l.codigo_linha != null && Number.isFinite(Number(l.codigo_linha))
      ? String(Math.trunc(Number(l.codigo_linha)))
      : String(l.id_linha);
  return l.descricao ? `${cod}-${l.descricao}` : cod;
}

function normalizeNrGuia(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, NR_MAX);
}

function dataHojeBR(): string {
  const hoje = new Date();
  const dd = String(hoje.getDate()).padStart(2, '0');
  const mm = String(hoje.getMonth() + 1).padStart(2, '0');
  const yyyy = hoje.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function extractHHMM(value: string | null | undefined): string {
  if (!value) return '';
  const m = String(value).match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : '';
}

function GuiaViagemOpsCard({
  viagem,
  acao,
  destaque,
  onOpen,
  onPrimary,
  primaryRef,
}: {
  viagem: GuiaViagemCard;
  acao?: ProximaAcaoTipo;
  destaque?: boolean;
  onOpen: () => void;
  onPrimary?: () => void;
  primaryRef?: React.Ref<HTMLButtonElement>;
}) {
  const op = statusOperacionalViagem(viagem);
  const sealTone =
    op === 'concluida' ? 'success' : op === 'em_transito' ? 'info' : 'warning';
  const motoristaTxt =
    viagem.matricula_motorista && viagem.motorista
      ? `${viagem.matricula_motorista} — ${viagem.motorista}`
      : viagem.motorista || viagem.matricula_motorista || null;
  const saidaReal = viagem.horario_saida_real || null;
  const desp = viagem.despachante_saida
    ? viagem.matricula_despachante_saida
      ? `${viagem.matricula_despachante_saida} — ${viagem.despachante_saida}`
      : viagem.despachante_saida
    : null;

  return (
    <OpsCard
      stripeClass={stripeClassStatusOperacional(op)}
      onClick={onOpen}
      aria-label={`${viagem.viagem_label}, ${viagem.sentido}, ${labelStatusOperacional(op)}`}
      className={destaque ? 'border-primary/30 ring-1 ring-primary/20' : undefined}
      primaryAction={
        acao && onPrimary ? (
          <PrimaryActionButton ref={primaryRef} onClick={onPrimary}>
            {labelProximaAcao(acao)}
          </PrimaryActionButton>
        ) : null
      }
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-bold text-foreground">
            <span className="tabular-nums">
              {viagem.viagem_label.replace(/^Viagem\s+/i, '')}
            </span>
            <span className="mx-1.5 text-border">·</span>
            <span>{viagem.veiculo}</span>
          </p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-0.5">
              <Clock3 className="h-3 w-3" aria-hidden />
              {saidaReal ? `Saída ${saidaReal}` : viagem.horario}
            </span>
            <span
              className={
                viagem.sentido === 'ida'
                  ? 'font-semibold text-sky-700'
                  : 'font-semibold text-teal-700'
              }
            >
              {viagem.sentido === 'ida' ? 'Ida' : 'Volta'}
            </span>
          </p>
          {op === 'em_transito' ? (
            <div className="mt-1.5 space-y-0.5 text-[11px] leading-snug text-slate-600">
              {motoristaTxt ? <p>Motorista: {motoristaTxt}</p> : null}
              {desp ? <p>Despachante: {desp}</p> : null}
            </div>
          ) : null}
        </div>
        <StatusSeal
          label={labelStatusOperacional(op)}
          tone={sealTone}
          icon={
            op === 'concluida' ? 'ok' : op === 'em_transito' ? 'tempo' : 'pendente'
          }
        />
      </div>
    </OpsCard>
  );
}

function emptyForm() {
  return {
    nrGuia: '',
    dataGuia: '',
    idEmpresa: '',
    idLinha: '',
    idTurno: '',
    carro: '',
    motorista: '',
    horarioPegada: '',
    horarioLargada: '',
    roletaInicial: '',
    roletaFinal: '',
    roleta2Inicial: '',
    roleta2Final: '',
    observacao: '',
    idItemMap: '',
    pasIda: '',
    pasVolta: '',
    ocorrencias: '',
  };
}

type FormState = ReturnType<typeof emptyForm>;

function montarPayload(state: FormState, opts?: { autoNumero?: boolean }): GuiaPayload {
  const payload: GuiaPayload = {
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
    numero: opts?.autoNumero ? '' : state.nrGuia.trim(),
  };
  return payload;
}

function validarFormulario(
  payload: GuiaPayload,
  opts?: { requireEscala?: boolean; autoNumero?: boolean },
): string | null {
  if (!opts?.autoNumero && !payload.numero.trim()) return 'Informe o NR(Guia).';
  if (!parseDateBR(payload.data.trim())) return 'Data inválida.';
  if (opts?.requireEscala && !payload.id_item_map) {
    return 'Selecione o mapa/turno e o carro/escala.';
  }
  const ini = payload.horario_pegada ?? '';
  const fim = payload.horario_largada ?? '';
  if (ini && !isValidHHMM(ini)) return 'INÍCIO(JORNADA) inválido.';
  if (fim && !isValidHHMM(fim)) return 'FIM(JORNADA) inválido.';
  const carro = payload.carro ?? '';
  const motorista = payload.motorista ?? '';
  if (carro && !/^\d{1,5}$/.test(carro)) {
    return 'Carro deve conter até 5 dígitos numéricos.';
  }
  if (motorista && !/^\d{1,5}$/.test(motorista)) {
    return 'Motorista deve conter até 5 dígitos numéricos.';
  }
  if ((payload.observacao ?? '').length > OBS_MAX) {
    return `Observação deve ter no máximo ${OBS_MAX} caracteres.`;
  }
  return null;
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

function apiMsg(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) {
    return err.body.mensagem || fallback;
  }
  return fallback;
}

function iniciaisNome(nome?: string | null): string {
  const parts = String(nome ?? '')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

/** Tela 08 — Guia mobile-first (RF-29..RF-51 + listagem do dia). */
export function GuiaScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(BG);
  const nrGuiaRef = useRef<HTMLInputElement>(null);
  const aliveRef = useRef(true);

  const [dataFiltro, setDataFiltro] = useState(dataHojeBR);
  const [guias, setGuias] = useState<Guia[]>([]);
  const [viagens, setViagens] = useState<GuiaViagemCard[]>([]);
  const [resumo, setResumo] = useState<GuiaResumoDia>({
    titulo_mapa: 'Guia do dia',
    ida: { jae: 0, riocard: 0 },
    volta: { jae: 0, riocard: 0 },
    total_viagens: 0,
    ultima_leitura: null,
  });
  const [syncStatus, setSyncStatus] = useState<GuiaSyncStatus>('sincronizado');
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [cadLoading, setCadLoading] = useState(true);

  const [filtroOpen, setFiltroOpen] = useState(false);
  const [filtroSentido, setFiltroSentido] = useState<FiltroSentido>('todos');
  const [filtroOrigem, setFiltroOrigem] = useState<FiltroOrigem>('todos');
  const [filtroPendentes, setFiltroPendentes] = useState(false);

  const [formOpen, setFormOpen] = useState(false);
  const [modo, setModo] = useState<GuiaModo>('idle');
  const [idGuia, setIdGuia] = useState<number | null>(null);
  const [cardAtivo, setCardAtivo] = useState<GuiaViagemCard | null>(null);
  const [busy, setBusy] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [pesquisarOpen, setPesquisarOpen] = useState(false);
  const [pesquisarNumero, setPesquisarNumero] = useState('');
  const [ajusteOpen, setAjusteOpen] = useState(false);
  const [justificativa, setJustificativa] = useState('');
  const [ajusteEmbarques, setAjusteEmbarques] = useState('');
  const [ajusteSentido, setAjusteSentido] = useState<SentidoViagem>('ida');
  const [alertaDetalheOpen, setAlertaDetalheOpen] = useState(false);
  const [roletaOpen, setRoletaOpen] = useState(false);
  const [roletaFonte, setRoletaFonte] = useState<GuiaFonteRoleta>('jae');
  const [roletaIni, setRoletaIni] = useState('');
  const [roletaFim, setRoletaFim] = useState('');
  const [roletaViradaJust, setRoletaViradaJust] = useState('');

  const [nrGuia, setNrGuia] = useState('');
  const [dataGuia, setDataGuia] = useState('');
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
  const [, setConfirmadoEscala] = useState(false);
  const [mapasOpcoes, setMapasOpcoes] = useState<GuiaMapaOpcao[]>([]);
  const [escalasOpcoes, setEscalasOpcoes] = useState<GuiaEscalaOpcao[]>([]);
  const [idMapaSel, setIdMapaSel] = useState('');
  const [contextoEscala, setContextoEscala] = useState<GuiaContextoEscala | null>(
    null,
  );
  const [escalasLoading, setEscalasLoading] = useState(false);
  const [alteracaoOpen, setAlteracaoOpen] = useState(false);
  const [saidaOpen, setSaidaOpen] = useState(false);
  const [saidaViagem, setSaidaViagem] = useState<GuiaViagemCard | null>(null);
  const saidaTriggerRef = useRef<HTMLButtonElement | null>(null);
  const [altCarro, setAltCarro] = useState('');
  const [altMotorista, setAltMotorista] = useState('');
  const [altHorIni, setAltHorIni] = useState('');
  const [altHorFim, setAltHorFim] = useState('');
  const [altChegada, setAltChegada] = useState('');
  const [altJustificativa, setAltJustificativa] = useState('');
  const [guiaStatus, setGuiaStatus] = useState<string | null>(null);
  const [guiaTrechos, setGuiaTrechos] = useState<GuiaTrecho[]>([]);
  const [guiaAlteracoes, setGuiaAlteracoes] = useState<GuiaAlteracao[]>([]);
  const [trocaRecursoOpen, setTrocaRecursoOpen] = useState(false);
  const [trocaCampo, setTrocaCampo] = useState<'veiculo' | 'linha'>('veiculo');
  const [trocaValor, setTrocaValor] = useState('');
  const [trocaMotivo, setTrocaMotivo] = useState('');
  const [encerrarOpen, setEncerrarOpen] = useState(false);
  const [encerrarHorFim, setEncerrarHorFim] = useState('');
  const [viagemDetalheOpen, setViagemDetalheOpen] = useState(false);
  const [detalheTrecho, setDetalheTrecho] = useState<GuiaTrecho | null>(null);
  const [detalheHorSaida, setDetalheHorSaida] = useState('');
  const [detalheHorChegada, setDetalheHorChegada] = useState('');
  const [detalheOcorrencias, setDetalheOcorrencias] = useState('');
  const [proximaViagemOpen, setProximaViagemOpen] = useState(false);
  const [proximaSentido, setProximaSentido] = useState<SentidoViagem>('ida');
  const [historicoJaE, setHistoricoJaE] = useState<GuiaRoletaHistoricoItem[]>([]);
  const [historicoRio, setHistoricoRio] = useState<GuiaRoletaHistoricoItem[]>([]);
  const [historicoLoading, setHistoricoLoading] = useState(false);

  const podeAlterarEscala = canAccessMapas(user?.codigo_perfil);

  const formState: FormState = {
    nrGuia,
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
  };

  const camposHabilitados = (modo === 'include' || modo === 'edit') && !busy;
  const salvarHabilitado = (modo === 'include' || modo === 'edit') && !busy;
  const deletarHabilitado = modo === 'edit' && idGuia != null && !busy;
  const jornadaAberta =
    modo === 'edit' &&
    idGuia != null &&
    String(guiaStatus || '').toUpperCase() !== 'ENCERRADA' &&
    !busy;
  const modoNovaComEscala = modo === 'include';

  const aplicarFormulario = useCallback((values: FormState) => {
    setNrGuia(values.nrGuia ?? '');
    setDataGuia(values.dataGuia ?? '');
    setIdEmpresa(values.idEmpresa ?? '');
    setIdLinha(values.idLinha ?? '');
    setIdTurno(values.idTurno ?? '');
    setCarro(values.carro ?? '');
    setMotorista(values.motorista ?? '');
    setHorarioPegada(values.horarioPegada ?? '');
    setHorarioLargada(values.horarioLargada ?? '');
    setRoletaInicial(values.roletaInicial ?? '');
    setRoletaFinal(values.roletaFinal ?? '');
    setRoleta2Inicial(values.roleta2Inicial ?? '');
    setRoleta2Final(values.roleta2Final ?? '');
    setObservacao(values.observacao ?? '');
    setIdItemMap(values.idItemMap ?? '');
    setPasIda(values.pasIda ?? '');
    setPasVolta(values.pasVolta ?? '');
    setOcorrencias(values.ocorrencias ?? '');
  }, []);

  const aplicarGuia = useCallback(
    (guia: Guia, nextModo: GuiaModo = 'edit') => {
      setIdGuia(guia.id_guia);
      setGuiaStatus(guia.status ?? (guia.hor_fim ? 'ENCERRADA' : 'ABERTA'));
      setGuiaTrechos(guia.trechos ?? []);
      setGuiaAlteracoes(guia.alteracoes ?? []);
      aplicarFormulario({
        nrGuia: guia.numero ?? '',
        dataGuia:
          toDateBR(guia.hor_ini ?? guia.hor_fim ?? guia.data ?? undefined) ||
          dataFiltro,
        idEmpresa: guia.id_empresa != null ? String(guia.id_empresa) : '',
        idLinha: guia.id_linha != null ? String(guia.id_linha) : '',
        idTurno: guia.id_turno != null ? String(guia.id_turno) : '',
        carro: guia.numero_frota ?? '',
        motorista: guia.matricula_motorista ?? '',
        horarioPegada: extractHHMM(guia.hor_ini),
        horarioLargada: extractHHMM(guia.hor_fim),
        roletaInicial: guia.roleta01_ini != null ? String(guia.roleta01_ini) : '',
        roletaFinal: guia.roleta01_fim != null ? String(guia.roleta01_fim) : '',
        roleta2Inicial: guia.roleta2_ini != null ? String(guia.roleta2_ini) : '',
        roleta2Final: guia.roleta2_fim != null ? String(guia.roleta2_fim) : '',
        observacao: guia.observacao ?? '',
        idItemMap: guia.id_item_map != null ? String(guia.id_item_map) : '',
        pasIda: '',
        pasVolta: '',
        ocorrencias: '',
      });
      setModo(nextModo);
      if (guia.id_item_map != null) {
        void getContextoEscala(guia.id_item_map)
          .then((r) => {
            if (aliveRef.current) setContextoEscala(r.contexto);
          })
          .catch(() => {
            if (aliveRef.current) setContextoEscala(null);
          });
      } else {
        setContextoEscala(null);
      }
    },
    [aplicarFormulario, dataFiltro],
  );

  const resetIdle = useCallback(() => {
    setModo('idle');
    setIdGuia(null);
    setGuiaStatus(null);
    setGuiaTrechos([]);
    setGuiaAlteracoes([]);
    aplicarFormulario(emptyForm());
    setContextoEscala(null);
    setMapasOpcoes([]);
    setEscalasOpcoes([]);
    setIdMapaSel('');
    setConfirmadoEscala(false);
    setAlteracaoOpen(false);
    setTrocaRecursoOpen(false);
    setEncerrarOpen(false);
  }, [aplicarFormulario]);

  const carregarLista = useCallback(async () => {
    if (!aliveRef.current) return;
    setListLoading(true);
    setListError(null);
    try {
      const data = await listGuias({
        data: dataFiltro,
        sentido: filtroSentido,
        origem: filtroOrigem === 'mapa' ? 'mapa' : filtroOrigem,
        pendencias: filtroPendentes,
      });
      if (!aliveRef.current) return;
      setGuias(data.guias ?? []);
      setViagens(data.viagens ?? []);
      setResumo(
        data.resumo ?? {
          titulo_mapa: 'Guia do dia',
          ida: { jae: 0, riocard: 0 },
          volta: { jae: 0, riocard: 0 },
          total_viagens: 0,
          ultima_leitura: null,
        },
      );
      setSyncStatus(data.status ?? 'sincronizado');
      if (data.erro_integracao) {
        setListError(data.erro_integracao);
      }
    } catch (e) {
      if (!aliveRef.current) return;
      setGuias([]);
      setViagens([]);
      setListError(
        e instanceof ApiRequestError
          ? e.status === 405
            ? e.body.mensagem ||
              'Consulta da Guia não disponível (método não permitido). Reinicie a API.'
            : e.body.mensagem || e.message
          : 'Não foi possível carregar as guias.',
      );
      setSyncStatus('falha');
    } finally {
      if (aliveRef.current) setListLoading(false);
    }
  }, [dataFiltro, filtroSentido, filtroOrigem, filtroPendentes]);

  useEffect(() => {
    aliveRef.current = true;
    void carregarLista();
    return () => {
      aliveRef.current = false;
    };
  }, [carregarLista]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getCadastros();
        if (!cancelled) setCadastros(data.cadastros);
      } catch {
        if (!cancelled) setCadastros(null);
      } finally {
        if (!cancelled) setCadLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const linhasFiltradas = (cadastros?.linhas ?? []).filter((l) =>
    idEmpresa ? String(l.id_empresa) === idEmpresa : true,
  );

  const filtrosAtivos =
    filtroSentido !== 'todos' || filtroOrigem !== 'todos' || filtroPendentes;

  const gruposViagens = useMemo(
    () => agruparViagensOperacionais(viagens),
    [viagens],
  );

  const filtroChips = useMemo(() => {
    const chips: { id: string; label: string; onClear: () => void }[] = [];
    if (filtroSentido !== 'todos') {
      chips.push({
        id: 'sentido',
        label: filtroSentido === 'ida' ? 'Ida' : 'Volta',
        onClear: () => setFiltroSentido('todos'),
      });
    }
    if (filtroOrigem !== 'todos') {
      chips.push({
        id: 'origem',
        label: `Origem: ${filtroOrigem}`,
        onClear: () => setFiltroOrigem('todos'),
      });
    }
    if (filtroPendentes) {
      chips.push({
        id: 'pendentes',
        label: 'Só pendentes',
        onClear: () => setFiltroPendentes(false),
      });
    }
    return chips;
  }, [filtroSentido, filtroOrigem, filtroPendentes]);

  const abrirNovo = () => {
    navigate('/guia/nova');
  };

  const carregarHistoricoViagem = async (card: GuiaViagemCard) => {
    setHistoricoLoading(true);
    setHistoricoJaE([]);
    setHistoricoRio([]);
    try {
      const tasks: Promise<void>[] = [];
      if (card.jae?.id_leitura != null) {
        tasks.push(
          getHistoricoRoleta(card.jae.id_leitura).then((r) => {
            if (aliveRef.current) setHistoricoJaE(r.historico ?? []);
          }),
        );
      }
      if (card.riocard?.id_leitura != null) {
        tasks.push(
          getHistoricoRoleta(card.riocard.id_leitura).then((r) => {
            if (aliveRef.current) setHistoricoRio(r.historico ?? []);
          }),
        );
      }
      await Promise.all(tasks);
    } catch {
      /* histórico opcional — detalhe ainda abre */
    } finally {
      if (aliveRef.current) setHistoricoLoading(false);
    }
  };

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
      // Carros só após escolher o mapa — API devolve escalas vazias sem id_mapa
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

  const aplicarContextoNoForm = (ctx: GuiaContextoEscala) => {
    setContextoEscala(ctx);
    setIdItemMap(String(ctx.id_item));
    setIdEmpresa(ctx.id_empresa != null ? String(ctx.id_empresa) : '');
    setIdLinha(ctx.id_linha != null ? String(ctx.id_linha) : '');
    setIdTurno(ctx.id_turno != null ? String(ctx.id_turno) : '');
    setCarro(ctx.numero_frota ? String(ctx.numero_frota) : '');
    setMotorista(ctx.matricula_motorista ? String(ctx.matricula_motorista) : '');
    if (ctx.data) setDataGuia(ctx.data);
    setConfirmadoEscala(false);
  };

  const selecionarEscala = async (idItemStr: string) => {
    if (!idItemStr) {
      setIdItemMap('');
      setContextoEscala(null);
      setConfirmadoEscala(false);
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

  const abrirDetalhe = (card: GuiaViagemCard) => {
    setCardAtivo(card);
    setIdGuia(card.id_guia ?? null);
    setAjusteSentido(card.sentido);
    setAjusteEmbarques(String(card.embarques ?? ''));
    setDetalheHorSaida(card.horario_saida ?? extractHHMM(card.horario) ?? '');
    setDetalheHorChegada(card.horario_chegada ?? '');
    setDetalheOcorrencias(card.ocorrencias || card.observacao || '');
    setDetalheTrecho(null);
    setViagemDetalheOpen(true);
    void carregarHistoricoViagem(card);
    if (card.id_guia != null) {
      void (async () => {
        try {
          const data = await getGuia(card.id_guia!);
          if (!aliveRef.current) return;
          const trechos = data.guia.trechos ?? [];
          const sent = card.sentido.toUpperCase();
          let match: GuiaTrecho | undefined;
          if (card.id_trecho != null) {
            match = trechos.find((t) => t.id_trecho === card.id_trecho);
          }
          if (!match) {
            match = trechos.find(
              (t) => String(t.sentido || '').toUpperCase() === sent,
            );
          }
          if (!match && trechos.length) {
            match = [...trechos].sort(
              (a, b) => Number(b.seq ?? 0) - Number(a.seq ?? 0),
            )[0];
          }
          setDetalheTrecho(match ?? null);
          if (match?.hor_ini) setDetalheHorSaida(extractHHMM(match.hor_ini));
          if (match?.hor_fim) setDetalheHorChegada(extractHHMM(match.hor_fim));
          setGuiaStatus(data.guia.status ?? null);
          setGuiaTrechos(trechos);
        } catch {
          /* detalhe ainda abre sem trecho */
        }
      })();
    }
  };

  const guiaAbertaDoDia = (): Guia | null => {
    const abertas = guias.filter(
      (g) => String(g.status || '').toUpperCase() !== 'ENCERRADA',
    );
    if (!abertas.length) return null;
    return abertas[0];
  };

  const abrirRegistrarProximaViagem = () => {
    const guia = guiaAbertaDoDia();
    if (!guia) {
      navigate('/guia/nova');
      return;
    }
    const lastSent = viagens[viagens.length - 1]?.sentido;
    setProximaSentido(lastSent === 'ida' ? 'volta' : 'ida');
    setProximaViagemOpen(true);
  };

  const confirmarProximaViagem = async () => {
    const guia = guiaAbertaDoDia();
    if (!guia || busy) return;
    setBusy(true);
    try {
      const data = await criarTrechoGuia(guia.id_guia, {
        sentido: proximaSentido === 'ida' ? 'IDA' : 'VOLTA',
        id_linha: guia.id_linha ?? undefined,
        id_veiculo: guia.id_veiculo ?? undefined,
        numero_frota: guia.numero_frota ?? undefined,
      });
      setProximaViagemOpen(false);
      setInfoMsg(data.mensagem ?? 'Próxima viagem registrada.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível registrar a próxima viagem.'));
    } finally {
      setBusy(false);
    }
  };

  const salvarDetalheViagem = async () => {
    if (!cardAtivo || busy) return;
    setBusy(true);
    try {
      if (detalheTrecho) {
        await atualizarTrechoGuia(detalheTrecho.id_trecho, {
          hor_ini: detalheHorSaida.trim() || undefined,
          hor_fim: detalheHorChegada.trim() || undefined,
          versao: detalheTrecho.versao ?? undefined,
          motivo: 'Atualização de horários no detalhe da viagem',
        });
      }
      if (cardAtivo.id_guia != null) {
        const det = await getGuia(cardAtivo.id_guia);
        const g = det.guia;
        await updateGuia(cardAtivo.id_guia, {
          numero: g.numero,
          data:
            toDateBR(g.hor_ini ?? g.hor_fim ?? g.data ?? undefined) || dataFiltro,
          id_empresa: g.id_empresa ?? undefined,
          id_linha: g.id_linha ?? undefined,
          id_turno: g.id_turno ?? undefined,
          id_veiculo: g.id_veiculo ?? undefined,
          id_item_map: g.id_item_map ?? undefined,
          numero_frota: g.numero_frota ?? undefined,
          matricula_motorista: g.matricula_motorista ?? undefined,
          hor_ini: extractHHMM(g.hor_ini) || undefined,
          hor_fim: extractHHMM(g.hor_fim) || undefined,
          roleta01_ini: g.roleta01_ini ?? undefined,
          roleta01_fim: g.roleta01_fim ?? undefined,
          roleta2_ini: g.roleta2_ini ?? undefined,
          roleta2_fim: g.roleta2_fim ?? undefined,
          observacao: detalheOcorrencias.trim().slice(0, OBS_MAX),
        });
      }
      setInfoMsg('Viagem atualizada.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível salvar o detalhe.'));
    } finally {
      setBusy(false);
    }
  };

  const pesquisarPorNumero = async (numero: string) => {
    const alvo = numero.trim();
    if (!alvo) {
      setInfoMsg('Informe o número da guia.');
      return;
    }
    setBusy(true);
    try {
      const data = await getGuiaByNumero(alvo);
      setCardAtivo(null);
      aplicarGuia(data.guia, 'edit');
      setPesquisarOpen(false);
      setPesquisarNumero('');
      setFormOpen(true);
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Guia não encontrada.'));
    } finally {
      setBusy(false);
    }
  };

  const salvar = async () => {
    if (busy || (modo !== 'include' && modo !== 'edit')) return;
    const autoNumero = modo === 'include';
    const body = montarPayload(formState, { autoNumero });
    const erroLocal = validarFormulario(body, {
      requireEscala: modo === 'include',
      autoNumero,
    });
    if (erroLocal) {
      setInfoMsg(erroLocal);
      return;
    }

    setBusy(true);
    try {
      if (idGuia != null) {
        const data = await updateGuia(idGuia, body);
        aplicarGuia(data.guia, 'edit');
        setInfoMsg(data.mensagem ?? 'Guia atualizada com sucesso.');
        await carregarLista();
        return;
      }
      const data = await createGuia(body);
      aplicarGuia(data.guia, 'edit');
      setInfoMsg(data.mensagem ?? MSG_CADASTRO_OK);
      await carregarLista();
    } catch (err) {
      if (idGuia == null) {
        setInfoMsg(MSG_CADASTRO_ERRO);
      } else {
        setInfoMsg(apiMsg(err, 'Não foi possível salvar a guia.'));
      }
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
      if (dataGuia) void carregarEscalasDoDia(dataGuia, idMapaSel ? Number(idMapaSel) : undefined);
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível alterar a escala.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmarTrocaRecurso = async () => {
    if (busy || idGuia == null) return;
    const motivo = trocaMotivo.trim();
    if (motivo.length < 5) {
      setInfoMsg('Informe o motivo da troca (mín. 5 caracteres).');
      return;
    }
    if (!trocaValor.trim()) {
      setInfoMsg(
        trocaCampo === 'veiculo' ? 'Informe o novo carro.' : 'Informe a nova linha.',
      );
      return;
    }
    setBusy(true);
    try {
      const data = await registrarAlteracaoGuia(idGuia, {
        campo: trocaCampo,
        motivo,
        numero_frota: trocaCampo === 'veiculo' ? trocaValor.trim() : undefined,
        id_linha:
          trocaCampo === 'linha' && Number.isFinite(Number(trocaValor))
            ? Number(trocaValor)
            : undefined,
      });
      aplicarGuia(data.guia, 'edit');
      setTrocaRecursoOpen(false);
      setTrocaMotivo('');
      setTrocaValor('');
      setInfoMsg(data.mensagem ?? 'Alteração registrada com auditoria.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível registrar a troca.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmarEncerrarJornada = async () => {
    if (busy || idGuia == null) return;
    const fim = encerrarHorFim.trim();
    if (fim && !isValidHHMM(fim)) {
      setInfoMsg('FIM(JORNADA) inválido.');
      return;
    }
    setBusy(true);
    try {
      const data = await encerrarGuia(idGuia, {
        ...(fim ? { hor_fim: fim } : {}),
        motivo_tipo: 'fim_jornada',
        motivo: 'Encerramento ao fim da jornada',
      });
      aplicarGuia(data.guia, 'edit');
      setEncerrarOpen(false);
      setInfoMsg(data.mensagem ?? 'Guia encerrada.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível encerrar a guia.'));
    } finally {
      setBusy(false);
    }
  };

  const acaoTrecho = async (
    trecho: GuiaTrecho,
    acao: 'iniciar' | 'concluir' | 'cancelar',
  ) => {
    if (busy || !podeAlterarEscala) return;
    if (acao === 'cancelar') {
      const motivo = window.prompt('Motivo do cancelamento do trecho:');
      if (!motivo || motivo.trim().length < 5) {
        setInfoMsg('Informe o motivo do cancelamento (mín. 5 caracteres).');
        return;
      }
      setBusy(true);
      try {
        const data = await cancelarTrechoGuia(trecho.id_trecho, {
          motivo: motivo.trim(),
          versao: trecho.versao ?? undefined,
        });
        if (idGuia != null) {
          const det = await getGuia(idGuia);
          aplicarGuia(det.guia, 'edit');
        }
        setInfoMsg(data.mensagem ?? 'Trecho cancelado.');
      } catch (err) {
        setInfoMsg(apiMsg(err, 'Não foi possível cancelar o trecho.'));
      } finally {
        setBusy(false);
      }
      return;
    }
    setBusy(true);
    try {
      if (acao === 'iniciar') {
        const saida =
          detalheHorSaida.trim() ||
          window.prompt('SAÍDA real (HH:MM)', '') ||
          '';
        if (!saida.trim()) {
          setInfoMsg('Informe a SAÍDA real do trecho.');
          setBusy(false);
          return;
        }
        const data = await iniciarTrechoGuia(trecho.id_trecho, {
          hor_ini: saida.trim(),
          versao: trecho.versao ?? undefined,
        });
        if (idGuia != null) {
          const det = await getGuia(idGuia);
          aplicarGuia(det.guia, 'edit');
        }
        setInfoMsg(data.mensagem ?? 'Trecho iniciado.');
      } else {
        const chegada =
          detalheHorChegada.trim() ||
          window.prompt('CHEGADA real (HH:MM)', '') ||
          '';
        if (!chegada.trim()) {
          setInfoMsg('Informe a CHEGADA real do trecho.');
          setBusy(false);
          return;
        }
        const data = await concluirTrechoGuia(trecho.id_trecho, {
          hor_fim: chegada.trim(),
          versao: trecho.versao ?? undefined,
        });
        if (idGuia != null) {
          const det = await getGuia(idGuia);
          aplicarGuia(det.guia, 'edit');
        }
        setInfoMsg(data.mensagem ?? 'Trecho concluído.');
      }
      if (detalheTrecho && detalheTrecho.id_trecho === trecho.id_trecho) {
        try {
          const det = await getGuia(idGuia ?? trecho.id_guia);
          const t = (det.guia.trechos ?? []).find(
            (x) => x.id_trecho === trecho.id_trecho,
          );
          setDetalheTrecho(t ?? null);
          setGuiaTrechos(det.guia.trechos ?? []);
        } catch {
          /* ignore */
        }
      }
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível atualizar o trecho.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmarAjusteManual = async () => {
    if (busy || idGuia == null) return;
    const just = justificativa.trim();
    if (!just) {
      setInfoMsg('Informe a justificativa do ajuste manual.');
      return;
    }
    const emb = Number(ajusteEmbarques);
    if (!Number.isFinite(emb) || emb < 0) {
      setInfoMsg('Informe os embarques do ajuste.');
      return;
    }
    setBusy(true);
    try {
      const data = await registrarAjusteManual(idGuia, {
        sentido: ajusteSentido,
        embarques: emb,
        justificativa: just,
      });
      aplicarGuia(data.guia, 'edit');
      setAjusteOpen(false);
      setJustificativa('');
      setInfoMsg(data.mensagem ?? 'Ajuste manual registrado com auditoria.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível registrar o ajuste.'));
    } finally {
      setBusy(false);
    }
  };

  const abrirRoleta = (card: GuiaViagemCard, fonte: GuiaFonteRoleta) => {
    setCardAtivo(card);
    setRoletaFonte(fonte);
    const bloco: GuiaRoletaBloco | null | undefined =
      fonte === 'jae' ? card.jae : card.riocard;
    const ini = bloco?.leitura_ini ?? bloco?.sugestao_ini ?? null;
    setRoletaIni(ini != null ? String(ini) : '');
    setRoletaFim(bloco?.leitura_fim != null ? String(bloco.leitura_fim) : '');
    setRoletaViradaJust(bloco?.justificativa_virada ?? '');
    setRoletaOpen(true);
  };

  const salvarLeituraRoleta = async () => {
    if (!cardAtivo || busy) return;
    if (cardAtivo.id_viagem == null && cardAtivo.id_guia == null) {
      setInfoMsg('Vínculo de viagem/guia ausente para registrar a leitura.');
      return;
    }
    const ini = roletaIni.trim() === '' ? null : Number(roletaIni);
    const fim = roletaFim.trim() === '' ? null : Number(roletaFim);
    if (ini == null || !Number.isFinite(ini)) {
      setInfoMsg('Informe a leitura inicial.');
      return;
    }
    if (fim != null && !Number.isFinite(fim)) {
      setInfoMsg('Leitura final inválida.');
      return;
    }
    if (fim != null && fim < ini && !roletaViradaJust.trim()) {
      setInfoMsg(
        'Leitura final menor que a inicial: informe a justificativa da virada.',
      );
      return;
    }
    setBusy(true);
    try {
      await salvarRoletaLeitura({
        id_viagem: cardAtivo.id_viagem,
        id_guia: cardAtivo.id_guia,
        id_trecho: cardAtivo.id_trecho ?? detalheTrecho?.id_trecho,
        id_veiculo: cardAtivo.id_veiculo,
        sentido: cardAtivo.sentido,
        fonte: roletaFonte,
        leitura_ini: ini,
        leitura_fim: fim,
        justificativa_virada: roletaViradaJust.trim() || undefined,
      });
      setRoletaOpen(false);
      setInfoMsg('Leitura registrada com sucesso.');
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível salvar a leitura.'));
    } finally {
      setBusy(false);
    }
  };

  const RoletaMini = ({
    titulo,
    bloco,
    onEdit,
  }: {
    titulo: string;
    bloco?: GuiaRoletaBloco | null;
    onEdit: () => void;
  }) => {
    const pas =
      bloco?.passageiros != null
        ? bloco.passageiros
        : bloco?.leitura_ini != null &&
            bloco?.leitura_fim != null &&
            bloco.leitura_fim >= bloco.leitura_ini
          ? bloco.leitura_fim - bloco.leitura_ini
          : '—';
    return (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onEdit();
        }}
        className="w-full rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-left"
        aria-label={`Editar ${titulo}`}
      >
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-700">
          {titulo}
        </p>
        <div className="mt-1 grid grid-cols-3 gap-1 text-[11px] text-slate-600">
          <span>
            Início{' '}
            <strong className="tabular-nums text-slate-900">
              {bloco?.leitura_ini ?? bloco?.sugestao_ini ?? '—'}
            </strong>
          </span>
          <span>
            Fim{' '}
            <strong className="tabular-nums text-slate-900">
              {bloco?.leitura_fim ?? '—'}
            </strong>
          </span>
          <span>
            Pas.{' '}
            <strong className="tabular-nums text-slate-900">{pas}</strong>
          </span>
        </div>
      </button>
    );
  };


  const deletar = async () => {
    if (!deletarHabilitado || idGuia == null) return;
    setBusy(true);
    try {
      await deleteGuia(idGuia);
      resetIdle();
      setFormOpen(false);
      setInfoMsg(MSG_EXCLUSAO_OK);
      await carregarLista();
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível excluir a guia.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-foreground">
        <PageHeader
          title="Guia"
          onBack={() => navigate('/principal')}
          rightSlot={
            <span
              className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-foreground/15 text-xs font-bold text-primary-foreground"
              aria-label={`Usuário ${user?.nome ?? ''}`}
              title={user?.nome ?? undefined}
            >
              {iniciaisNome(user?.nome)}
            </span>
          }
        />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-3 pb-[calc(var(--main-tab-bar)+env(safe-area-inset-bottom,0px)+5.5rem)]">
          <div className="flex gap-2">
            <button
              type="button"
              className="flex min-h-11 flex-1 items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 text-left text-sm font-medium text-slate-800"
              aria-label={`Data selecionada: ${formatDataChip(dataFiltro)}`}
              onClick={() => {
                const next = window.prompt('Data (dd/mm/aaaa)', dataFiltro);
                if (next == null) return;
                if (!parseDateBR(next.trim())) {
                  setInfoMsg('Data inválida.');
                  return;
                }
                setDataFiltro(next.trim());
              }}
            >
              <CalendarDays className="h-4 w-4 shrink-0 text-slate-600" aria-hidden />
              <span className="truncate">{formatDataChip(dataFiltro)}</span>
            </button>
          </div>

          {listLoading || cadLoading ? (
            <LoadingState label="Carregando guias…" />
          ) : listError ? (
            <ErrorState
              title="Falha ao sincronizar"
              message={listError}
              onRetry={() => void carregarLista()}
            />
          ) : (
            <>
              <section
                className="surface-card rounded-2xl px-3.5 py-3"
                aria-label="Resumo da guia"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h2 className="truncate text-base font-bold text-slate-900">
                      {resumo.titulo_mapa}
                      {resumo.turno ? (
                        <span className="font-semibold text-slate-600">
                          {' '}
                          · {resumo.turno}
                        </span>
                      ) : null}
                    </h2>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      <StatusSeal
                        label={labelStatusGuia(syncStatus)}
                        tone={
                          syncStatus === 'sincronizado'
                            ? 'success'
                            : syncStatus === 'atualizando'
                              ? 'info'
                              : 'warning'
                        }
                        icon={
                          syncStatus === 'sincronizado'
                            ? 'ok'
                            : syncStatus === 'atualizando'
                              ? 'tempo'
                              : 'alerta'
                        }
                      />
                      <StatusSeal
                        label={`${resumo.total_viagens} viagem${resumo.total_viagens === 1 ? '' : 's'}`}
                        tone="neutral"
                        icon="viagem"
                      />
                      <StatusSeal
                        label={`${resumo.total_pendente ?? contarPendentesOperacionais(viagens)} pendente${(resumo.total_pendente ?? contarPendentesOperacionais(viagens)) === 1 ? '' : 's'}`}
                        tone="warning"
                        icon="pendente"
                      />
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-9 w-9"
                      aria-label="Pesquisar guia"
                      onClick={() => {
                        setPesquisarNumero('');
                        setPesquisarOpen(true);
                      }}
                    >
                      <Search className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-9 w-9"
                      aria-label="Nova guia"
                      onClick={abrirNovo}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </section>

              <FilterChipsBar
                chips={filtroChips}
                filterActive={filtrosAtivos}
                onOpenFilters={() => setFiltroOpen(true)}
              />

              {syncStatus !== 'sincronizado' ? (
                <AlertPanel
                  tone={
                    syncStatus === 'falha' || syncStatus === 'divergencia'
                      ? 'danger'
                      : 'warning'
                  }
                  title={
                    syncStatus === 'falha'
                      ? 'Falha de sincronização'
                      : syncStatus === 'divergencia'
                        ? 'Divergência para revisar'
                        : syncStatus === 'manual'
                          ? 'Há ajuste(s) manual(is)'
                          : syncStatus === 'atualizando'
                            ? 'Atualizando leituras'
                            : 'Pendências na Guia'
                  }
                  description="Status consolidado a partir de Mapa, Viagens e Roleta."
                  action={
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="border-slate-300 bg-white"
                      onClick={() => setAlertaDetalheOpen(true)}
                    >
                      Ver
                    </Button>
                  }
                />
              ) : null}

              {viagens.length === 0 ? (
                <EmptyState
                  title="Nenhuma viagem"
                  description={
                    filtrosAtivos
                      ? 'Nenhum registro com os filtros atuais.'
                      : 'Não há viagens/guias para a data selecionada.'
                  }
                  action={
                    <Button type="button" onClick={abrirNovo}>
                      Nova guia
                    </Button>
                  }
                />
              ) : (
                <div className="flex flex-col gap-4">
                  {gruposViagens.proxima ? (
                    <section aria-label="Próxima ação" className="space-y-2">
                      <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-primary">
                        Próxima ação
                      </h3>
                      <GuiaViagemOpsCard
                        viagem={gruposViagens.proxima.viagem}
                        acao={gruposViagens.proxima.acao}
                        destaque
                        primaryRef={saidaTriggerRef}
                        onOpen={() => abrirDetalhe(gruposViagens.proxima!.viagem)}
                        onPrimary={() => {
                          const p = gruposViagens.proxima!;
                          if (p.acao === 'registrar_saida') {
                            setSaidaViagem(p.viagem);
                            setSaidaOpen(true);
                            return;
                          }
                          abrirDetalhe(p.viagem);
                        }}
                      />
                    </section>
                  ) : null}

                  {(
                    [
                      ['Em trânsito', gruposViagens.emTransito],
                      ['Pendentes', gruposViagens.pendentes],
                      ['Concluídas', gruposViagens.concluidas],
                    ] as const
                  ).map(([titulo, lista]) =>
                    lista.length === 0 ? null : (
                      <section
                        key={titulo}
                        aria-label={titulo}
                        className="space-y-2"
                      >
                        <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-slate-600">
                          {titulo}
                          <span className="ml-1 font-semibold tabular-nums text-slate-400">
                            ({lista.length})
                          </span>
                        </h3>
                        <ul className="flex flex-col gap-2">
                          {lista.map((v) => {
                            const acaoLista =
                              titulo === 'Em trânsito'
                                ? ('registrar_chegada' as const)
                                : titulo === 'Pendentes'
                                  ? ('registrar_saida' as const)
                                  : undefined;
                            return (
                              <li key={v.key}>
                                <GuiaViagemOpsCard
                                  viagem={v}
                                  acao={acaoLista}
                                  onOpen={() => abrirDetalhe(v)}
                                  onPrimary={
                                    acaoLista === 'registrar_saida'
                                      ? () => {
                                          setSaidaViagem(v);
                                          setSaidaOpen(true);
                                        }
                                      : acaoLista === 'registrar_chegada'
                                        ? () => abrirDetalhe(v)
                                        : undefined
                                  }
                                />
                              </li>
                            );
                          })}
                        </ul>
                      </section>
                    ),
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <div className="pointer-events-none fixed bottom-[calc(var(--main-tab-bar)+env(safe-area-inset-bottom,0px))] left-1/2 z-30 w-full max-w-phone -translate-x-1/2 px-3 pb-2">
          <Button
            type="button"
            className="pointer-events-auto h-12 w-full rounded-xl text-sm font-bold shadow-lg"
            aria-label="Registrar próxima viagem"
            onClick={abrirRegistrarProximaViagem}
            disabled={busy || listLoading}
          >
            <Bus className="mr-2 h-4 w-4" aria-hidden />
            Registrar próxima viagem
          </Button>
        </div>

        <AlertDialog
          open={infoMsg !== null}
          message={infoMsg ?? ''}
          onConfirm={() => setInfoMsg(null)}
        />

        <RegistrarSaidaPanel
          open={saidaOpen}
          onOpenChange={setSaidaOpen}
          viagem={saidaViagem}
          triggerRef={saidaTriggerRef}
          onSuccess={() => {
            setInfoMsg('Saída registrada. Viagem em trânsito.');
            void carregarLista();
          }}
          onTrocaMotorista={(guia, viagem) => {
            const idItem = guia.id_item_map ?? viagem.id_item_map;
            if (idItem == null) {
              setInfoMsg(
                'Troca de motorista exige escala vinculada (id_item_map).',
              );
              return;
            }
            setIdItemMap(String(idItem));
            setAltCarro(
              String(viagem.numero_frota || viagem.veiculo || guia.numero_frota || ''),
            );
            setAltMotorista(String(viagem.matricula_motorista || guia.matricula_motorista || ''));
            setAltHorIni('');
            setAltHorFim('');
            setAltChegada('');
            setAltJustificativa('');
            setSaidaOpen(false);
            setAlteracaoOpen(true);
          }}
        />

        <Dialog open={filtroOpen} onOpenChange={setFiltroOpen}>
          <DialogContent className="max-w-[360px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Filtrar
              </DialogTitle>
            </DialogHeader>
            <div className="mt-3 space-y-3">
              <div>
                <Label className="mb-1.5 block text-sm font-semibold">Sentido</Label>
                <Select
                  value={filtroSentido}
                  onValueChange={(v) => setFiltroSentido(v as FiltroSentido)}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos</SelectItem>
                    <SelectItem value="ida">Ida</SelectItem>
                    <SelectItem value="volta">Volta</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="mb-1.5 block text-sm font-semibold">Origem</Label>
                <Select
                  value={filtroOrigem}
                  onValueChange={(v) => setFiltroOrigem(v as FiltroOrigem)}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todas</SelectItem>
                    <SelectItem value="roleta">Roleta</SelectItem>
                    <SelectItem value="manual">Manual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={filtroPendentes}
                  onChange={(e) => setFiltroPendentes(e.target.checked)}
                  className="h-4 w-4"
                />
                Somente pendências / ajustes
              </label>
            </div>
            <DialogFooter className="mt-4 flex gap-2 sm:justify-between">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setFiltroSentido('todos');
                  setFiltroOrigem('todos');
                  setFiltroPendentes(false);
                }}
              >
                Limpar
              </Button>
              <Button type="button" className="flex-1" onClick={() => setFiltroOpen(false)}>
                Aplicar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={pesquisarOpen} onOpenChange={setPesquisarOpen}>
          <DialogContent className="max-w-[340px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide text-slate-900">
                Pesquisar guia
              </DialogTitle>
            </DialogHeader>
            <div className="mt-2">
              <Label
                htmlFor="pesquisa_nr_guia"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                NR(Guia)
              </Label>
              <Input
                id="pesquisa_nr_guia"
                inputMode="numeric"
                autoComplete="off"
                maxLength={NR_MAX}
                value={pesquisarNumero}
                onChange={(e) => setPesquisarNumero(normalizeNrGuia(e.target.value))}
                className="h-12 rounded-lg border-slate-400 bg-white text-base text-slate-900"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    void pesquisarPorNumero(pesquisarNumero);
                  }
                }}
              />
            </div>
            <DialogFooter className="mt-5">
              <Button
                type="button"
                className="w-full"
                disabled={busy || !pesquisarNumero.trim()}
                onClick={() => void pesquisarPorNumero(pesquisarNumero)}
              >
                OK
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={alertaDetalheOpen} onOpenChange={setAlertaDetalheOpen}>
          <DialogContent className="max-w-[380px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Divergências
              </DialogTitle>
            </DialogHeader>
            <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto">
              {viagens
                .filter((v) => v.status !== 'sincronizado')
                .map((v) => (
                  <li key={`div-${v.key}`}>
                    <button
                      type="button"
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm"
                      onClick={() => {
                        setAlertaDetalheOpen(false);
                        abrirDetalhe(v);
                      }}
                    >
                      <span className="font-semibold">{v.viagem_label}</span>
                      {' — '}
                      {labelStatusGuia(v.status)}
                    </button>
                  </li>
                ))}
              {viagens.every((v) => v.status === 'sincronizado') ? (
                <li className="text-sm text-slate-600">Nenhum item pendente na lista.</li>
              ) : null}
            </ul>
          </DialogContent>
        </Dialog>

        <Dialog
          open={viagemDetalheOpen}
          onOpenChange={(open) => {
            setViagemDetalheOpen(open);
            if (!open) {
              setHistoricoJaE([]);
              setHistoricoRio([]);
              setDetalheTrecho(null);
            }
          }}
        >
          <DialogContent className="flex max-h-[92dvh] max-w-[420px] flex-col gap-0 overflow-hidden border-slate-400/50 bg-screen p-0">
            <DialogHeader className="border-b border-slate-200 px-4 py-3">
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                {cardAtivo?.viagem_label ?? 'Detalhe da viagem'}
              </DialogTitle>
            </DialogHeader>
            {cardAtivo ? (
              <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold',
                      cardAtivo.sentido === 'ida'
                        ? 'bg-sky-100 text-sky-800'
                        : 'bg-teal-100 text-teal-800',
                    )}
                  >
                    {cardAtivo.sentido === 'ida' ? 'Ida' : 'Volta'}
                  </span>
                  <StatusBadge
                    label={labelStatusOperacional(
                      statusOperacionalViagem({
                        ...cardAtivo,
                        trecho_status:
                          detalheTrecho?.status ?? cardAtivo.trecho_status,
                      }),
                    )}
                    tone={
                      statusOperacionalViagem({
                        ...cardAtivo,
                        trecho_status:
                          detalheTrecho?.status ?? cardAtivo.trecho_status,
                      }) === 'concluida'
                        ? 'success'
                        : statusOperacionalViagem({
                              ...cardAtivo,
                              trecho_status:
                                detalheTrecho?.status ?? cardAtivo.trecho_status,
                            }) === 'em_transito'
                          ? 'warning'
                          : 'warning'
                    }
                    className="normal-case tracking-normal"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <ReadonlyField label="Veículo" value={cardAtivo.veiculo} />
                  <ReadonlyField
                    label="Linha"
                    value={
                      cardAtivo.linha ||
                      (cardAtivo.codigo_linha != null
                        ? String(cardAtivo.codigo_linha)
                        : null) ||
                      cardAtivo.mapa
                    }
                  />
                  <ReadonlyField
                    label="Motorista"
                    value={
                      cardAtivo.matricula_motorista
                        ? `${cardAtivo.matricula_motorista}${
                            cardAtivo.motorista
                              ? ` — ${cardAtivo.motorista}`
                              : ''
                          }`
                        : cardAtivo.motorista
                    }
                  />
                  <ReadonlyField
                    label="Responsável"
                    value={
                      cardAtivo.responsavel ||
                      cardAtivo.jae?.nome_usuario ||
                      cardAtivo.riocard?.nome_usuario
                    }
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <FormField
                    label="Saída"
                    name="detalhe_hor_saida"
                    type="time"
                    value={detalheHorSaida}
                    onChange={(e) => setDetalheHorSaida(e.target.value)}
                    className={halfFieldClass}
                    disabled={busy || !detalheTrecho}
                  />
                  <FormField
                    label="Chegada"
                    name="detalhe_hor_chegada"
                    type="time"
                    value={detalheHorChegada}
                    onChange={(e) => setDetalheHorChegada(e.target.value)}
                    className={halfFieldClass}
                    disabled={busy || !detalheTrecho}
                  />
                </div>

                <p className="text-center text-[13px] font-semibold uppercase tracking-wide text-slate-700">
                  Leituras (independentes)
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <RoletaMini
                    titulo="Ja E"
                    bloco={cardAtivo.jae}
                    onEdit={() => {
                      setViagemDetalheOpen(false);
                      abrirRoleta(cardAtivo, 'jae');
                    }}
                  />
                  <RoletaMini
                    titulo="RioCard"
                    bloco={cardAtivo.riocard}
                    onEdit={() => {
                      setViagemDetalheOpen(false);
                      abrirRoleta(cardAtivo, 'riocard');
                    }}
                  />
                </div>

                <div>
                  <Label className={labelClass} htmlFor="detalhe_ocorrencias">
                    Ocorrências
                  </Label>
                  <textarea
                    id="detalhe_ocorrencias"
                    value={detalheOcorrencias}
                    onChange={(e) =>
                      setDetalheOcorrencias(e.target.value.slice(0, OBS_MAX))
                    }
                    disabled={busy}
                    rows={3}
                    className={cn(
                      fieldClass,
                      'mt-1.5 min-h-[4rem] w-full resize-y px-3 py-2 text-sm',
                    )}
                  />
                </div>

                {detalheTrecho && podeAlterarEscala ? (
                  <div className="flex flex-wrap gap-2">
                    {String(detalheTrecho.status).toUpperCase() === 'PLANEJADO' ? (
                      <>
                        <Button
                          type="button"
                          size="sm"
                          disabled={busy}
                          onClick={() => void acaoTrecho(detalheTrecho, 'iniciar')}
                        >
                          Iniciar trecho
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="destructive"
                          disabled={busy}
                          onClick={() => void acaoTrecho(detalheTrecho, 'cancelar')}
                        >
                          Cancelar
                        </Button>
                      </>
                    ) : null}
                    {String(detalheTrecho.status).toUpperCase() === 'EM_TRANSITO' ? (
                      <>
                        <Button
                          type="button"
                          size="sm"
                          disabled={busy}
                          onClick={() => void acaoTrecho(detalheTrecho, 'concluir')}
                        >
                          Concluir trecho
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="destructive"
                          disabled={busy}
                          onClick={() => void acaoTrecho(detalheTrecho, 'cancelar')}
                        >
                          Cancelar
                        </Button>
                      </>
                    ) : null}
                  </div>
                ) : null}

                <div>
                  <p className={`${labelClass} mb-1`}>Histórico</p>
                  {historicoLoading ? (
                    <p className="text-sm text-slate-500">Carregando…</p>
                  ) : historicoJaE.length === 0 && historicoRio.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      Sem histórico de leituras nesta viagem.
                    </p>
                  ) : (
                    <ul className="max-h-40 space-y-2 overflow-y-auto text-sm">
                      {historicoJaE.map((h, i) => (
                        <li
                          key={`jae-h-${h.id_historico ?? i}`}
                          className="rounded border border-slate-200 bg-white px-2 py-1.5"
                        >
                          <span className="font-semibold text-sky-800">Ja E</span>
                          {' · '}
                          {h.acao ?? '—'}
                          {h.nome_usuario ? ` · ${h.nome_usuario}` : ''}
                          {h.registrado_em
                            ? ` · ${extractHHMM(h.registrado_em) || h.registrado_em}`
                            : ''}
                        </li>
                      ))}
                      {historicoRio.map((h, i) => (
                        <li
                          key={`rio-h-${h.id_historico ?? i}`}
                          className="rounded border border-slate-200 bg-white px-2 py-1.5"
                        >
                          <span className="font-semibold text-teal-800">
                            RioCard
                          </span>
                          {' · '}
                          {h.acao ?? '—'}
                          {h.nome_usuario ? ` · ${h.nome_usuario}` : ''}
                          {h.registrado_em
                            ? ` · ${extractHHMM(h.registrado_em) || h.registrado_em}`
                            : ''}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : null}
            <div className="flex flex-wrap gap-2 border-t border-slate-200 bg-white/80 p-3">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                disabled={cardAtivo?.id_guia == null || busy}
                onClick={() => {
                  setAjusteSentido(cardAtivo?.sentido ?? 'ida');
                  setAjusteEmbarques(
                    cardAtivo != null ? String(cardAtivo.embarques) : '',
                  );
                  setJustificativa('');
                  setAjusteOpen(true);
                }}
              >
                Ajuste manual
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                disabled={busy}
                onClick={() => void salvarDetalheViagem()}
              >
                Salvar
              </Button>
              <Button
                type="button"
                className="flex-1"
                onClick={() => setViagemDetalheOpen(false)}
              >
                Fechar
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={proximaViagemOpen} onOpenChange={setProximaViagemOpen}>
          <DialogContent className="max-w-[380px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Registrar próxima viagem
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              Cria um novo trecho na guia aberta do dia
              {guiaAbertaDoDia()?.numero
                ? ` (${guiaAbertaDoDia()?.numero})`
                : ''}
              .
            </p>
            <div className="mt-3 flex w-full flex-col gap-1.5">
              <Label className={labelClass}>Sentido</Label>
              <Select
                value={proximaSentido}
                onValueChange={(v) => setProximaSentido(v as SentidoViagem)}
              >
                <SelectTrigger className={selectTriggerClass} aria-label="Sentido">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ida">Ida</SelectItem>
                  <SelectItem value="volta">Volta</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter className="mt-4 gap-2 sm:justify-center">
              <Button
                type="button"
                variant="outline"
                onClick={() => setProximaViagemOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy}
                onClick={() => void confirmarProximaViagem()}
              >
                Confirmar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) {
              resetIdle();
              setAjusteOpen(false);
              setJustificativa('');
            }
          }}
        >
          <DialogContent className="flex max-h-[92dvh] max-w-[420px] flex-col gap-0 overflow-hidden border-slate-400/50 bg-screen p-0">
            <DialogHeader className="border-b border-slate-200 px-4 py-3">
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                {modo === 'include' ? 'Nova guia' : 'Detalhe da guia'}
              </DialogTitle>
            </DialogHeader>
            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
              {modoNovaComEscala ? (
                <ReadonlyField
                  label="NR(Guia)"
                  value="Gerado automaticamente ao salvar"
                />
              ) : (
                <FormField
                  ref={nrGuiaRef}
                  label="NR(Guia)"
                  name="nr_guia"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="off"
                  maxLength={NR_MAX}
                  value={nrGuia}
                  onChange={(e) => setNrGuia(normalizeNrGuia(e.target.value))}
                  className={fieldClass}
                  disabled
                />
              )}

              <DatePickerField
                label="Data"
                name="data_guia"
                value={dataGuia}
                onChange={(v) => {
                  setDataGuia(v);
                  if (modoNovaComEscala) {
                    setIdMapaSel('');
                    setIdItemMap('');
                    setContextoEscala(null);
                    setConfirmadoEscala(false);
                    setEscalasOpcoes([]);
                    void carregarEscalasDoDia(v);
                  }
                }}
                iconBesideLabel
                inputClassName="h-10 text-sm shadow-none"
                disabled={!camposHabilitados || modo === 'edit'}
              />

              {modoNovaComEscala ? (
                <>
                  <div className="flex w-full flex-col gap-1.5">
                    <Label className={labelClass}>Mapa / Turno</Label>
                    <Select
                      value={toSelectValue(idMapaSel)}
                      onValueChange={(v) => {
                        const id = fromSelectValue(v);
                        setIdMapaSel(id);
                        setIdItemMap('');
                        setContextoEscala(null);
                        setConfirmadoEscala(false);
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
                          <SelectItem
                            key={m.id_registro}
                            value={String(m.id_registro)}
                          >
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
                      onValueChange={(v) =>
                        void selecionarEscala(fromSelectValue(v))
                      }
                      disabled={
                        !camposHabilitados || !idMapaSel || escalasLoading
                      }
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
                          <SelectItem
                            key={e.id_item}
                            value={String(e.id_item)}
                          >
                            {e.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </>
              ) : null}

              {contextoEscala ? (
                <div className="space-y-3 rounded-xl border border-slate-300 bg-white/70 p-3">
                  <p className="text-center text-[13px] font-semibold uppercase tracking-wide text-slate-700">
                    Dados da escala (somente leitura)
                  </p>
                  <div className="grid grid-cols-2 gap-2">
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
                        setAltMotorista(
                          contextoEscala.matricula_motorista ?? '',
                        );
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

              {!modoNovaComEscala && !contextoEscala ? (
                <>
                  <div className="flex w-full flex-col gap-1.5">
                    <Label className={labelClass}>Empresa</Label>
                    <Select
                      value={toSelectValue(idEmpresa)}
                      onValueChange={(v) => {
                        setIdEmpresa(fromSelectValue(v));
                        setIdLinha('');
                      }}
                      disabled={!camposHabilitados}
                    >
                      <SelectTrigger className={selectTriggerClass}>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                          Selecione
                        </SelectItem>
                        {(cadastros?.empresas ?? []).map((e) => (
                          <SelectItem
                            key={e.id_empresa}
                            value={String(e.id_empresa)}
                          >
                            {e.descricao}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex w-full flex-col gap-1.5">
                      <Label className={labelClass}>Linha</Label>
                      <Select
                        value={toSelectValue(idLinha)}
                        onValueChange={(v) => setIdLinha(fromSelectValue(v))}
                        disabled={!camposHabilitados}
                      >
                        <SelectTrigger className={selectTriggerClass}>
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem
                            value={SELECT_EMPTY}
                            disabled
                            className="hidden"
                          >
                            Selecione
                          </SelectItem>
                          {linhasFiltradas.map((l) => (
                            <SelectItem
                              key={l.id_linha}
                              value={String(l.id_linha)}
                            >
                              {formatLinhaLabel(l)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex w-full flex-col gap-1.5">
                      <Label className={labelClass}>Turno</Label>
                      <Select
                        value={toSelectValue(idTurno)}
                        onValueChange={(v) => setIdTurno(fromSelectValue(v))}
                        disabled={!camposHabilitados}
                      >
                        <SelectTrigger className={selectTriggerClass}>
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem
                            value={SELECT_EMPTY}
                            disabled
                            className="hidden"
                          >
                            Selecione
                          </SelectItem>
                          {(cadastros?.turnos ?? []).map((t) => (
                            <SelectItem
                              key={t.id_turno}
                              value={String(t.id_turno)}
                            >
                              {t.descricao}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField
                      label="Carro"
                      name="carro"
                      type="tel"
                      inputMode="numeric"
                      maxLength={5}
                      value={carro}
                      onChange={(e) => setCarro(onlyDigits(e.target.value, 5))}
                      className={halfFieldClass}
                      disabled={!camposHabilitados}
                    />
                    <FormField
                      label="Motorista"
                      name="motorista"
                      type="tel"
                      inputMode="numeric"
                      maxLength={5}
                      value={motorista}
                      onChange={(e) =>
                        setMotorista(onlyDigits(e.target.value, 5))
                      }
                      className={halfFieldClass}
                      disabled={!camposHabilitados}
                    />
                  </div>
                </>
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
                <Label className={labelClass} htmlFor="ocorrencias_guia">
                  Ocorrências
                </Label>
                <textarea
                  id="ocorrencias_guia"
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
                <Label className={labelClass} htmlFor="observacao_guia">
                  Observações
                </Label>
                <textarea
                  id="observacao_guia"
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

              {modo === 'edit' && guiaStatus ? (
                <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800">
                  Status da jornada:{' '}
                  <span className="font-semibold">
                    {String(guiaStatus).toUpperCase() === 'ENCERRADA'
                      ? 'Encerrada'
                      : 'Aberta'}
                  </span>
                  {guiaTrechos.length > 0
                    ? ` · ${guiaTrechos.length} trecho(s)`
                    : null}
                </p>
              ) : null}

              {guiaTrechos.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-[13px] font-semibold uppercase tracking-wide text-slate-700">
                    Trechos da jornada
                  </p>
                  <ul className="max-h-40 space-y-1 overflow-y-auto text-sm text-slate-700">
                    {guiaTrechos.map((t) => (
                      <li
                        key={t.id_trecho}
                        className="rounded border border-slate-200 bg-white px-2 py-1.5"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span>
                            #{t.seq ?? t.id_trecho} {t.sentido ?? '—'} ·{' '}
                            {t.status ?? '—'} · Linha{' '}
                            {t.codigo_linha ?? t.id_linha ?? '—'} · Frota{' '}
                            {t.numero_frota ?? '—'}
                            {t.total_jae != null ? ` · Ja E ${t.total_jae}` : ''}
                            {t.total_riocard != null
                              ? ` · RioCard ${t.total_riocard}`
                              : ''}
                          </span>
                          {jornadaAberta && podeAlterarEscala ? (
                            <span className="flex gap-1">
                              {String(t.status).toUpperCase() === 'EM_TRANSITO' ? (
                                <>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    disabled={busy}
                                    onClick={() => void acaoTrecho(t, 'concluir')}
                                  >
                                    Concluir
                                  </Button>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="destructive"
                                    disabled={busy}
                                    onClick={() => void acaoTrecho(t, 'cancelar')}
                                  >
                                    Cancelar
                                  </Button>
                                </>
                              ) : null}
                              {String(t.status).toUpperCase() === 'PLANEJADO' ? (
                                <>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    disabled={busy}
                                    onClick={() => void acaoTrecho(t, 'iniciar')}
                                  >
                                    Iniciar
                                  </Button>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="destructive"
                                    disabled={busy}
                                    onClick={() => void acaoTrecho(t, 'cancelar')}
                                  >
                                    Cancelar
                                  </Button>
                                </>
                              ) : null}
                            </span>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {guiaAlteracoes.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-[13px] font-semibold uppercase tracking-wide text-slate-700">
                    Histórico de trocas
                  </p>
                  <ul className="max-h-32 space-y-1 overflow-y-auto text-xs text-slate-600">
                    {guiaAlteracoes.map((a) => (
                      <li key={a.id_alteracao}>
                        {a.campo}: {a.valor_anterior || '—'} → {a.valor_novo || '—'}{' '}
                        ({a.motivo})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-2 border-t border-slate-200 bg-white/80 p-3">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                disabled={!jornadaAberta || !podeAlterarEscala}
                onClick={() => {
                  setTrocaCampo('veiculo');
                  setTrocaValor(carro);
                  setTrocaMotivo('');
                  setTrocaRecursoOpen(true);
                }}
              >
                Trocar carro/linha
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                disabled={!jornadaAberta}
                onClick={() => {
                  setEncerrarHorFim(horarioLargada || '');
                  setEncerrarOpen(true);
                }}
              >
                Encerrar jornada
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                disabled={!deletarHabilitado || idGuia == null}
                onClick={() => {
                  setAjusteSentido(cardAtivo?.sentido ?? 'ida');
                  setAjusteEmbarques(
                    cardAtivo != null ? String(cardAtivo.embarques) : '',
                  );
                  setJustificativa('');
                  setAjusteOpen(true);
                }}
              >
                Ajuste manual
              </Button>
              <Button
                type="button"
                className="flex-1"
                disabled={!salvarHabilitado}
                onClick={() => void salvar()}
              >
                Salvar
              </Button>
              <Button
                type="button"
                variant="destructive"
                className="flex-1"
                disabled={!deletarHabilitado}
                onClick={() => void deletar()}
              >
                Deletar
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={trocaRecursoOpen} onOpenChange={setTrocaRecursoOpen}>
          <DialogContent className="max-w-[380px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Troca na jornada
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              Troca linha ou carro sem encerrar a guia (mesma empresa). Exige motivo
              para auditoria.
            </p>
            <div className="mt-3 space-y-3">
              <div>
                <Label className="mb-1.5 block text-sm font-semibold">Campo</Label>
                <Select
                  value={trocaCampo}
                  onValueChange={(v) => setTrocaCampo(v as 'veiculo' | 'linha')}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="veiculo">Carro</SelectItem>
                    <SelectItem value="linha">Linha</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <FormField
                label={trocaCampo === 'veiculo' ? 'Novo carro (frota)' : 'Nova linha (id)'}
                name="troca_valor"
                type="tel"
                inputMode="numeric"
                value={trocaValor}
                onChange={(e) =>
                  setTrocaValor(
                    trocaCampo === 'veiculo'
                      ? onlyDigits(e.target.value, 8)
                      : onlyDigits(e.target.value),
                  )
                }
                className={fieldClass}
              />
              <div>
                <Label htmlFor="troca_motivo" className="mb-1.5 block text-sm font-semibold">
                  Motivo
                </Label>
                <textarea
                  id="troca_motivo"
                  rows={3}
                  maxLength={255}
                  value={trocaMotivo}
                  onChange={(e) => setTrocaMotivo(e.target.value)}
                  className={cn(fieldClass, 'min-h-[4rem] w-full resize-y px-3 py-2')}
                />
              </div>
            </div>
            <DialogFooter className="mt-4 gap-2">
              <Button type="button" variant="outline" onClick={() => setTrocaRecursoOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy || trocaMotivo.trim().length < 5 || !trocaValor.trim()}
                onClick={() => void confirmarTrocaRecurso()}
              >
                Confirmar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={encerrarOpen} onOpenChange={setEncerrarOpen}>
          <DialogContent className="max-w-[360px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Encerrar jornada
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              Encerre ao final do turno ou antes de mudar de empresa (Redentor /
              Futuro / Barra).
            </p>
            <FormField
              label="Fim(Jornada)"
              name="encerrar_hor_fim"
              type="text"
              inputMode="numeric"
              placeholder="HH:MM (agora se vazio)"
              value={encerrarHorFim}
              onChange={(e) => setEncerrarHorFim(maskHHMM(e.target.value))}
              className={cn(fieldClass, 'mt-3')}
            />
            <DialogFooter className="mt-4 gap-2">
              <Button type="button" variant="outline" onClick={() => setEncerrarOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy}
                onClick={() => void confirmarEncerrarJornada()}
              >
                Encerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={ajusteOpen} onOpenChange={setAjusteOpen}>
          <DialogContent className="max-w-[360px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                Ajuste manual
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              A roleta original não será sobrescrita. Informe sentido, embarques e
              justificativa para auditoria.
            </p>
            <div className="mt-3 space-y-3">
              <div>
                <Label className="mb-1.5 block text-sm font-semibold">Sentido</Label>
                <Select
                  value={ajusteSentido}
                  onValueChange={(v) => setAjusteSentido(v as SentidoViagem)}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ida">Ida</SelectItem>
                    <SelectItem value="volta">Volta</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <FormField
                label="Embarques"
                name="ajuste_embarques"
                type="tel"
                inputMode="numeric"
                value={ajusteEmbarques}
                onChange={(e) => setAjusteEmbarques(onlyDigits(e.target.value))}
                className={fieldClass}
              />
              <div>
                <Label htmlFor="justificativa_ajuste" className="mb-1.5 block text-sm font-semibold">
                  Justificativa
                </Label>
                <textarea
                  id="justificativa_ajuste"
                  rows={3}
                  maxLength={100}
                  value={justificativa}
                  onChange={(e) => setJustificativa(e.target.value)}
                  className={cn(fieldClass, 'min-h-[4rem] w-full resize-y px-3 py-2')}
                />
              </div>
            </div>
            <DialogFooter className="mt-4 gap-2">
              <Button type="button" variant="outline" onClick={() => setAjusteOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy || !justificativa.trim() || !ajusteEmbarques.trim()}
                onClick={() => void confirmarAjusteManual()}
              >
                Confirmar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

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
                  htmlFor="justificativa_escala"
                  className="mb-1.5 block text-sm font-semibold"
                >
                  Justificativa
                </Label>
                <textarea
                  id="justificativa_escala"
                  rows={3}
                  maxLength={300}
                  value={altJustificativa}
                  onChange={(e) => setAltJustificativa(e.target.value)}
                  className={cn(fieldClass, 'min-h-[4rem] w-full resize-y px-3 py-2')}
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

        <Dialog open={roletaOpen} onOpenChange={setRoletaOpen}>
          <DialogContent className="max-w-[360px] border-slate-400/50 bg-screen p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide">
                {roletaFonte === 'jae' ? 'Ja E' : 'RioCard'} —{' '}
                {cardAtivo?.sentido === 'volta' ? 'Volta' : 'Ida'}
              </DialogTitle>
            </DialogHeader>
            <p className="mt-2 text-sm text-slate-600">
              Inicie com a leitura inicial. Ao finalizar, informe a final — passageiros
              calculados automaticamente.
            </p>
            <div className="mt-3 space-y-3">
              <FormField
                label="Leitura inicial"
                name="roleta_ini"
                type="tel"
                inputMode="numeric"
                value={roletaIni}
                onChange={(e) => setRoletaIni(onlyDigits(e.target.value))}
                className={fieldClass}
              />
              <FormField
                label="Leitura final"
                name="roleta_fim"
                type="tel"
                inputMode="numeric"
                value={roletaFim}
                onChange={(e) => setRoletaFim(onlyDigits(e.target.value))}
                className={fieldClass}
              />
              {roletaIni &&
              roletaFim &&
              Number(roletaFim) < Number(roletaIni) ? (
                <div>
                  <Label
                    htmlFor="virada_just"
                    className="mb-1.5 block text-sm font-semibold text-red-700"
                  >
                    Justificativa da virada
                  </Label>
                  <textarea
                    id="virada_just"
                    rows={2}
                    maxLength={200}
                    value={roletaViradaJust}
                    onChange={(e) => setRoletaViradaJust(e.target.value)}
                    className={cn(fieldClass, 'min-h-[3.5rem] w-full resize-y px-3 py-2')}
                  />
                </div>
              ) : null}
              {roletaIni && roletaFim && Number(roletaFim) >= Number(roletaIni) ? (
                <p className="text-sm text-slate-700">
                  Passageiros:{' '}
                  <strong className="tabular-nums">
                    {Number(roletaFim) - Number(roletaIni)}
                  </strong>
                </p>
              ) : null}
            </div>
            <DialogFooter className="mt-4 gap-2">
              <Button type="button" variant="outline" onClick={() => setRoletaOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={busy || !roletaIni.trim()}
                onClick={() => void salvarLeituraRoleta()}
              >
                Salvar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
