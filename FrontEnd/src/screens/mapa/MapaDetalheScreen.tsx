import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Pencil, Plus, Trash2, UserPlus, X } from 'lucide-react';
import { toast } from 'sonner';
import { getCadastros, createVeiculo } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import {
  createItem,
  createViagem,
  darBaixaItem,
  deleteItem,
  deleteMapa,
  deleteViagem,
  getMapa,
  listOcupacaoEscalas,
  updateItem,
} from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
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
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useScreenBg } from '@/hooks/useScreenBg';
import { cn } from '@/lib/utils';
import type { CadastrosMestres, VeiculoCadastro } from '@/types/cadastro';
import type {
  MapaCompleto,
  MapaItem,
  MapaOcupacaoMotorista,
  MapaOcupacaoVeiculo,
} from '@/types/mapa';
import {
  combineDateAndTime,
  formatCodigoMapa,
  formatHora,
  fromDateTimeLocal,
  toDateInput,
  toDateTimeLocal,
} from '@/utils/mapaFormat';
import {
  normalizarFrotaDigitada,
  placeholderFrotaEmpresa,
  mascaraGuiaFrotaEmpresa,
  erroFrotaDuranteDigitacao,
  validarFrotaParaEmpresa,
} from '@/utils/frotaVeiculo';
import { SCREEN_BG } from '@/theme/tokens';

const MAPA_BG = SCREEN_BG;

const isAtivo = (ativo?: number) => ativo == null || Number(ativo) === 1;

const statusEscala = (item: { status_escala?: string | null }) =>
  String(item.status_escala ?? 'EM_ANDAMENTO').trim().toUpperCase() ||
  'EM_ANDAMENTO';

const escalaEmAndamento = (item: { status_escala?: string | null }) =>
  statusEscala(item) === 'EM_ANDAMENTO';

function nowDateTimeLocal(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function inicioRealItem(item: {
  inicio_real?: string | null;
  chegada_ponto?: string | null;
  hor_ini_jor?: string | null;
}): string | null {
  return item.inicio_real || item.chegada_ponto || item.hor_ini_jor || null;
}

function minutosEntreDateTimeLocal(
  inicioSqlOuLocal: string | null | undefined,
  fimLocal: string,
): number | null {
  if (!inicioSqlOuLocal || !fimLocal) return null;
  const a = toDateTimeLocal(inicioSqlOuLocal);
  if (!a) return null;
  const t0 = Date.parse(a);
  const t1 = Date.parse(fimLocal);
  if (Number.isNaN(t0) || Number.isNaN(t1) || t1 < t0) return null;
  return Math.floor((t1 - t0) / 60000);
}

function formatDuracaoHhMm(minutos: number | null | undefined): string {
  if (minutos == null || !Number.isFinite(minutos) || minutos < 0) return '—';
  const h = Math.floor(minutos / 60);
  const m = Math.floor(minutos % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function frotaItemLabel(item: MapaItem): string {
  return item.numero_frota
    ? String(item.numero_frota)
    : String(item.id_veiculo ?? '—');
}

function linhaItemLabel(item: MapaItem): string {
  if (item.codigo_linha != null) return String(item.codigo_linha);
  if (item.linha) return String(item.linha);
  if (item.id_linha != null) return String(item.id_linha);
  return '—';
}

function motoristaItemLabel(item: MapaItem): string {
  const mat = String(item.matricula_motorista ?? '').trim();
  const nome = String(item.motorista ?? '').trim();
  if (mat || nome) return [mat, nome].filter(Boolean).join(' — ');
  return '—';
}

function jornadaItemLabel(item: MapaItem): string {
  const ini = formatHora(item.hor_ini_jor);
  const fim = formatHora(item.hor_fim_jor);
  if (ini === '—' && fim === '—') return '—';
  return `${ini}–${fim}`;
}

function StatusEscalaBadge({
  item,
  className,
}: {
  item: { status_escala?: string | null; duracao_trabalhada_hhmm?: string | null; duracao_trabalhada_minutos?: number | null };
  className?: string;
}) {
  const emAndamento = escalaEmAndamento(item);
  return (
    <div className={cn('flex flex-col gap-0.5', className)}>
      <Badge
        variant={emAndamento ? 'warning' : 'success'}
        className="w-fit whitespace-nowrap text-[10px] uppercase"
      >
        {emAndamento ? 'Em andamento' : 'Encerrada'}
      </Badge>
      {!emAndamento ? (
        <span className="helper-text text-[10px] font-medium">
          Trabalhado:{' '}
          {item.duracao_trabalhada_hhmm ??
            formatDuracaoHhMm(item.duracao_trabalhada_minutos)}
        </span>
      ) : null}
    </div>
  );
}

/** Detalhe do MAPA — carros + viagens. Rota: `/mapas/:id` */
export function MapaDetalheScreen() {
  const navigate = useNavigate();
  const { id: idParam } = useParams();
  const idRegistro = Number(idParam);
  useScreenBg(MAPA_BG);

  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);

  const [motoristaDialog, setMotoristaDialog] = useState(false);
  const [viagemDialog, setViagemDialog] = useState(false);
  const [confirmDeleteMap, setConfirmDeleteMap] = useState(false);
  const [confirmDeleteItem, setConfirmDeleteItem] = useState(false);
  const [confirmDeleteViagem, setConfirmDeleteViagem] = useState<number | null>(null);
  const [confirmBaixaItem, setConfirmBaixaItem] = useState(false);
  const [fimRealBaixa, setFimRealBaixa] = useState('');
  const [busy, setBusy] = useState(false);
  const [vinculoSaving, setVinculoSaving] = useState(false);
  const [erroVinculo, setErroVinculo] = useState('');
  const [ocupacaoVeiculos, setOcupacaoVeiculos] = useState<MapaOcupacaoVeiculo[]>(
    [],
  );
  const [ocupacaoMotoristas, setOcupacaoMotoristas] = useState<
    MapaOcupacaoMotorista[]
  >([]);
  const [ocupacaoLoading, setOcupacaoLoading] = useState(false);
  const [ocupacaoErro, setOcupacaoErro] = useState(false);

  const [idEmpresaForm, setIdEmpresaForm] = useState('');
  const [idLinhaForm, setIdLinhaForm] = useState('');
  const [idVeiculoForm, setIdVeiculoForm] = useState('');
  /** Frota digitada manualmente (sempre maiúscula). */
  const [frotaQuery, setFrotaQuery] = useState('');
  const [frotaErro, setFrotaErro] = useState('');
  const veiculoInputRef = useRef<HTMLInputElement | null>(null);
  const [confirmCriarVeiculo, setConfirmCriarVeiculo] = useState(false);
  const [idMotorista, setIdMotorista] = useState('');
  const [editItemId, setEditItemId] = useState<number | null>(null);
  const [horIni, setHorIni] = useState('');
  const [horFim, setHorFim] = useState('');
  const [chegada, setChegada] = useState('');
  const [frotaContextoMotorista, setFrotaContextoMotorista] = useState('');
  const [empresaContextoMotorista, setEmpresaContextoMotorista] = useState('');
  const [linhaContextoMotorista, setLinhaContextoMotorista] = useState('');
  /** Remonta o form a cada abertura — evita Select/inputs com state residual. */
  const [motoristaFormKey, setMotoristaFormKey] = useState(0);
  const [motoristaDialogMode, setMotoristaDialogMode] = useState<'novo' | 'editar'>('novo');

  const [saidaHora, setSaidaHora] = useState('');
  const [chegadaHora, setChegadaHora] = useState('');
  const [qtdIda, setQtdIda] = useState('0');
  const [qtdVolta, setQtdVolta] = useState('0');
  const [erroViagem, setErroViagem] = useState('');

  const goLista = () => navigate('/mapas', { replace: true });

  const carregar = useCallback(async () => {
    if (!Number.isFinite(idRegistro)) {
      goLista();
      return;
    }
    setLoading(true);
    try {
      const [mapRes, cadRes] = await Promise.all([
        getMapa(idRegistro),
        getCadastros(),
      ]);
      const m = mapRes?.mapa;
      if (!m || m.id_registro == null) {
        throw new ApiRequestError(404, {
          ok: false,
          mensagem: 'MAPA não encontrado.',
          codigo: 'nao_encontrado',
        });
      }
      setMapa(m);
      setSelectedItemId((prev) => {
        if (prev != null && m.itens.some((i) => i.id_item === prev)) return prev;
        // Exige seleção explícita na lista CARROS (viagens pertencem ao item).
        return null;
      });
      setCadastros(cadRes.cadastros);
    } catch (e) {
      const msg =
        e instanceof ApiRequestError ? e.message : 'Falha de comunicação com a API.';
      toast.error(msg);
      goLista();
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- navigate estável
  }, [idRegistro]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const itemSelecionado = useMemo(
    () => mapa?.itens.find((i) => i.id_item === selectedItemId) ?? null,
    [mapa, selectedItemId],
  );

  /** Viagens apenas do item/escala selecionado (não por frota). */
  const viagensDoItem = useMemo(() => {
    if (!itemSelecionado) return [];
    const idItem = Number(itemSelecionado.id_item);
    return (itemSelecionado.viagens ?? []).filter(
      (v) =>
        Number(v.id_item_registro ?? v.id_mapa_item ?? 0) === idItem,
    );
  }, [itemSelecionado]);

  const itemProntoParaViagens = useMemo(() => {
    if (!itemSelecionado) return false;
    if (!escalaEmAndamento(itemSelecionado)) return false;
    const temVeiculo =
      itemSelecionado.id_veiculo != null &&
      Number(itemSelecionado.id_veiculo) > 0;
    const temMotorista =
      itemSelecionado.id_motorista != null &&
      Number(itemSelecionado.id_motorista) > 0;
    return temVeiculo && temMotorista;
  }, [itemSelecionado]);

  /** Última viagem do item (maior chegada) — base para sequência. */
  const ultimaViagemItem = useMemo(() => {
    if (viagensDoItem.length === 0) return null;
    const ranked = [...viagensDoItem].sort((a, b) => {
      const ta = Date.parse(String(a.horario_chegada).replace(' ', 'T')) || 0;
      const tb = Date.parse(String(b.horario_chegada).replace(' ', 'T')) || 0;
      return tb - ta;
    });
    return ranked[0] ?? null;
  }, [viagensDoItem]);

  const saidaMinimaViagem = useMemo(() => {
    if (!ultimaViagemItem) return null;
    const h = formatHora(ultimaViagemItem.horario_chegada);
    return h === '—' ? null : h;
  }, [ultimaViagemItem]);

  const conflitoViagemLocal = useMemo(() => {
    if (!saidaHora || !chegadaHora) return null;
    if (chegadaHora <= saidaHora) {
      return 'A chegada deve ser posterior à saída da viagem.';
    }
    if (saidaMinimaViagem && saidaHora < saidaMinimaViagem) {
      return `Informe uma saída a partir de ${saidaMinimaViagem}.`;
    }
    return null;
  }, [chegadaHora, saidaHora, saidaMinimaViagem]);

  const itemPodeDarBaixa = useMemo(
    () =>
      Boolean(
        itemSelecionado &&
          escalaEmAndamento(itemSelecionado) &&
          itemSelecionado.id_motorista != null &&
          Number(itemSelecionado.id_motorista) > 0,
      ),
    [itemSelecionado],
  );

  const resumoViagens = useMemo(() => {
    if (!itemSelecionado) return null;
    const frota = frotaItemLabel(itemSelecionado);
    const motoristaTxt = motoristaItemLabel(itemSelecionado);
    const linhaTxt = linhaItemLabel(itemSelecionado);
    const empresaTxt = String(itemSelecionado.empresa ?? '—');
    const jornadaTxt = (() => {
      const label = jornadaItemLabel(itemSelecionado);
      return label === '—' ? null : label;
    })();
    const inicioRealTxt = formatHora(inicioRealItem(itemSelecionado));
    const fimRealTxt = formatHora(
      itemSelecionado.fim_real ?? itemSelecionado.baixa_em,
    );
    const trabalhadoTxt =
      itemSelecionado.duracao_trabalhada_hhmm ??
      formatDuracaoHhMm(itemSelecionado.duracao_trabalhada_minutos);
    const emAndamento = escalaEmAndamento(itemSelecionado);
    return {
      frota,
      motoristaTxt,
      linhaTxt,
      empresaTxt,
      jornadaTxt,
      inicioRealTxt,
      fimRealTxt,
      trabalhadoTxt,
      encerrada: !emAndamento,
      statusLabel: emAndamento ? 'Em andamento' : 'Encerrada',
    };
  }, [itemSelecionado]);

  const previewBaixa = useMemo(() => {
    if (!itemSelecionado || !fimRealBaixa) {
      return { inicioHora: '—', fimHora: '—', duracao: '—', minutos: null as number | null };
    }
    const ini = inicioRealItem(itemSelecionado);
    const minutos = minutosEntreDateTimeLocal(ini, fimRealBaixa);
    return {
      inicioHora: formatHora(ini),
      fimHora: formatHora(fromDateTimeLocal(fimRealBaixa)),
      duracao: formatDuracaoHhMm(minutos),
      minutos,
    };
  }, [fimRealBaixa, itemSelecionado]);

  const abrirDialogBaixa = () => {
    setFimRealBaixa(nowDateTimeLocal());
    setConfirmBaixaItem(true);
  };


  const empresas = useMemo(
    () => (cadastros?.empresas ?? []).filter((e) => isAtivo(e.ativo)),
    [cadastros],
  );

  const linhasFiltradas = useMemo(() => {
    if (!idEmpresaForm) return [];
    return (cadastros?.linhas ?? []).filter(
      (l) => String(l.id_empresa) === idEmpresaForm && isAtivo(l.ativo),
    );
  }, [cadastros, idEmpresaForm]);

  const empresaSelecionada = useMemo(() => {
    if (!idEmpresaForm) return null;
    return (
      (cadastros?.empresas ?? []).find(
        (e) => String(e.id_empresa) === idEmpresaForm,
      ) ?? null
    );
  }, [cadastros, idEmpresaForm]);

  const nomeEmpresaForm = empresaSelecionada?.descricao ?? '';

  const idsVeiculosOcupados = useMemo(() => {
    const set = new Set<number>();
    for (const o of ocupacaoVeiculos) {
      const idItem = Number(o.id_mapa_item ?? o.id_item);
      if (editItemId != null && idItem === Number(editItemId)) continue;
      set.add(Number(o.id_veiculo));
    }
    return set;
  }, [ocupacaoVeiculos, editItemId]);

  const idsMotoristasOcupados = useMemo(() => {
    const set = new Set<number>();
    for (const o of ocupacaoMotoristas) {
      const idItem = Number(o.id_mapa_item ?? o.id_item);
      if (editItemId != null && idItem === Number(editItemId)) continue;
      set.add(Number(o.id_motorista));
    }
    return set;
  }, [ocupacaoMotoristas, editItemId]);

  const motivoVeiculoOcupado = useMemo(() => {
    if (motoristaDialogMode === 'editar' && idVeiculoForm) {
      const id = Number(idVeiculoForm);
      if (id > 0 && idsVeiculosOcupados.has(id)) {
        const frota = frotaQuery.trim().toUpperCase() || String(id);
        const occ = ocupacaoVeiculos.find((o) => Number(o.id_veiculo) === id);
        const mapaRef =
          formatCodigoMapa(occ?.codigo_mapa) !== '—'
            ? formatCodigoMapa(occ?.codigo_mapa)
            : null;
        return mapaRef != null
          ? `O veículo ${frota} está em operação no MAPA ${mapaRef}. Dê baixa antes de vinculá-lo novamente.`
          : `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`;
      }
      return null;
    }
    if (!frotaQuery.trim() || validarFrotaParaEmpresa(frotaQuery, nomeEmpresaForm)) {
      return null;
    }
    const existente = (cadastros?.veiculos ?? []).find((v) => {
      if (!isAtivo(v.ativo)) return false;
      if (String(v.id_empresa ?? '') !== idEmpresaForm) return false;
      return String(v.numero_frota ?? '').toUpperCase() === frotaQuery.trim().toUpperCase();
    });
    if (!existente) return null;
    if (!idsVeiculosOcupados.has(Number(existente.id_veiculo))) return null;
    const frota = frotaQuery.trim().toUpperCase();
    const occ = ocupacaoVeiculos.find(
      (o) => Number(o.id_veiculo) === Number(existente.id_veiculo),
    );
    const mapaRef =
      formatCodigoMapa(occ?.codigo_mapa) !== '—'
        ? formatCodigoMapa(occ?.codigo_mapa)
        : null;
    return mapaRef != null
      ? `O veículo ${frota} está em operação no MAPA ${mapaRef}. Dê baixa antes de vinculá-lo novamente.`
      : `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`;
  }, [
    cadastros,
    frotaQuery,
    idEmpresaForm,
    idVeiculoForm,
    idsVeiculosOcupados,
    motoristaDialogMode,
    nomeEmpresaForm,
    ocupacaoVeiculos,
  ]);

  const frotaValida =
    motoristaDialogMode === 'editar'
      ? Boolean(idVeiculoForm) && !motivoVeiculoOcupado
      : validarFrotaParaEmpresa(frotaQuery, nomeEmpresaForm) == null &&
        frotaQuery.trim().length > 0 &&
        !motivoVeiculoOcupado;

  const motoristas = useMemo(() => {
    if (motoristaDialogMode === 'novo' && !frotaValida) return [];
    if (motoristaDialogMode === 'editar' && !idVeiculoForm) return [];
    return (cadastros?.motoristas ?? [])
      .filter((m) => isAtivo(m.ativo))
      .map((m) => ({
        ...m,
        emOperacao: idsMotoristasOcupados.has(Number(m.id_motorista)),
      }));
  }, [
    cadastros,
    frotaValida,
    idVeiculoForm,
    idsMotoristasOcupados,
    motoristaDialogMode,
  ]);

  const carregarOcupacao = useCallback(async (): Promise<{
    ok: boolean;
    veiculos: MapaOcupacaoVeiculo[];
    motoristas: MapaOcupacaoMotorista[];
  }> => {
    setOcupacaoLoading(true);
    setOcupacaoErro(false);
    try {
      const res = await listOcupacaoEscalas();
      const veiculos = res.veiculos_ocupados ?? res.veiculos ?? [];
      const motoristasList = res.motoristas_ocupados ?? res.motoristas ?? [];
      setOcupacaoVeiculos(veiculos);
      setOcupacaoMotoristas(motoristasList);
      setOcupacaoErro(false);
      return { ok: true, veiculos, motoristas: motoristasList };
    } catch {
      setOcupacaoErro(true);
      toast.error(
        'Não foi possível verificar a disponibilidade de veículo e motorista. Verifique a conexão e tente novamente.',
      );
      return { ok: false, veiculos: [], motoristas: [] };
    } finally {
      setOcupacaoLoading(false);
    }
  }, []);

  useEffect(() => {
    if (
      !motoristaDialog ||
      motoristaDialogMode !== 'novo' ||
      !idEmpresaForm ||
      !idLinhaForm
    ) {
      return;
    }
    const t = window.setTimeout(() => veiculoInputRef.current?.focus(), 50);
    return () => window.clearTimeout(t);
  }, [
    motoristaDialog,
    motoristaDialogMode,
    idEmpresaForm,
    idLinhaForm,
    motoristaFormKey,
  ]);

  const limparHorariosMotorista = () => {
    // Mantém jornada do MAPA (não zera) — troca de motorista não apaga horários.
    if (!mapa) {
      setHorIni('');
      setHorFim('');
      setChegada('');
      return;
    }
    const iniMapa = toDateTimeLocal(mapa.inicio_jornada_des) ?? '';
    const fimMapa = toDateTimeLocal(mapa.fim_jornada_des) ?? '';
    setHorIni(iniMapa);
    setHorFim(fimMapa);
    setChegada(iniMapa);
  };

  const limparMotoristaEHorarios = () => {
    setIdMotorista('');
    limparHorariosMotorista();
  };

  const limparVeiculoEAbaixo = () => {
    setIdVeiculoForm('');
    setFrotaQuery('');
    setFrotaErro('');
    setConfirmCriarVeiculo(false);
    limparMotoristaEHorarios();
  };

  const limparLinhaEAbaixo = () => {
    setIdLinhaForm('');
    limparVeiculoEAbaixo();
  };

  const resetMotoristaForm = () => {
    setIdEmpresaForm('');
    setIdLinhaForm('');
    setIdVeiculoForm('');
    setFrotaQuery('');
    setFrotaErro('');
    setConfirmCriarVeiculo(false);
    setIdMotorista('');
    setEditItemId(null);
    setHorIni('');
    setHorFim('');
    setChegada('');
    setFrotaContextoMotorista('');
    setEmpresaContextoMotorista('');
    setLinhaContextoMotorista('');
    setMotoristaDialogMode('novo');
  };

  const closeMotoristaDialog = () => {
    setMotoristaDialog(false);
    setConfirmCriarVeiculo(false);
    setErroVinculo('');
    setVinculoSaving(false);
    resetMotoristaForm();
    setMotoristaFormKey((k) => k + 1);
  };

  const onFrotaQueryChange = (texto: string) => {
    const norm = normalizarFrotaDigitada(texto);
    setFrotaQuery(norm);
    setIdVeiculoForm('');
    setFrotaErro(erroFrotaDuranteDigitacao(norm, nomeEmpresaForm) ?? '');
    limparMotoristaEHorarios();
  };

  const buscarVeiculoPorFrota = (frota: string): VeiculoCadastro | null => {
    const q = frota.trim().toUpperCase();
    if (!q || !idEmpresaForm) return null;
    return (
      (cadastros?.veiculos ?? []).find((v) => {
        if (!isAtivo(v.ativo)) return false;
        if (String(v.id_empresa ?? '') !== idEmpresaForm) return false;
        return String(v.numero_frota ?? '').toUpperCase() === q;
      }) ?? null
    );
  };

  const openMotoristaNovo = () => {
    if (!mapa) return;
    resetMotoristaForm();
    setErroVinculo('');
    setOcupacaoErro(false);
    setVinculoSaving(false);
    setMotoristaDialogMode('novo');
    setEditItemId(null);
    // Pré-preenche jornada do MAPA para o usuário só ajustar se precisar.
    const iniMapa = toDateTimeLocal(mapa.inicio_jornada_des) ?? '';
    const fimMapa = toDateTimeLocal(mapa.fim_jornada_des) ?? '';
    setHorIni(iniMapa);
    setHorFim(fimMapa);
    setChegada(iniMapa);
    setMotoristaFormKey((k) => k + 1);
    setMotoristaDialog(true);
    void carregarOcupacao();
  };

  const openMotoristaEditar = (idItem: number) => {
    if (!mapa) return;
    const itemAlvo = mapa.itens.find(
      (i) => String(i.id_item) === String(idItem),
    );
    if (!itemAlvo) {
      toast.error('Carro não encontrado neste MAPA.');
      return;
    }
    if (!escalaEmAndamento(itemAlvo)) {
      toast.error('Esta escala foi encerrada e não pode ser alterada.');
      return;
    }
    const vinculado =
      itemAlvo.id_motorista != null && Number(itemAlvo.id_motorista) > 0;
    if (!vinculado) {
      toast.error('Este carro ainda não tem motorista vinculado.');
      return;
    }

    let idEmpresa =
      itemAlvo.id_empresa != null ? String(itemAlvo.id_empresa) : '';
    if (!idEmpresa && cadastros) {
      const linhaCad = cadastros.linhas.find(
        (l) => Number(l.id_linha) === Number(itemAlvo.id_linha),
      );
      if (linhaCad) idEmpresa = String(linhaCad.id_empresa);
      else {
        const veicCad = cadastros.veiculos.find(
          (v) => Number(v.id_veiculo) === Number(itemAlvo.id_veiculo),
        );
        if (veicCad?.id_empresa != null) idEmpresa = String(veicCad.id_empresa);
      }
    }

    const formInicio = toDateTimeLocal(itemAlvo.hor_ini_jor) ?? '';
    const formFim = toDateTimeLocal(itemAlvo.hor_fim_jor) ?? '';
    const formChegada = toDateTimeLocal(itemAlvo.chegada_ponto) ?? '';

    setSelectedItemId(itemAlvo.id_item);
    setEditItemId(itemAlvo.id_item);
    setIdEmpresaForm(idEmpresa);
    setIdLinhaForm(
      itemAlvo.id_linha != null ? String(itemAlvo.id_linha) : '',
    );
    setIdVeiculoForm(
      itemAlvo.id_veiculo != null ? String(itemAlvo.id_veiculo) : '',
    );
    setFrotaQuery(String(itemAlvo.numero_frota ?? itemAlvo.id_veiculo ?? ''));
    setFrotaErro('');
    setConfirmCriarVeiculo(false);
    setIdMotorista(
      itemAlvo.id_motorista != null ? String(itemAlvo.id_motorista) : '',
    );
    setHorIni(formInicio);
    setHorFim(formFim);
    setChegada(formChegada);
    setFrotaContextoMotorista(
      String(itemAlvo.numero_frota ?? itemAlvo.id_veiculo ?? ''),
    );
    setEmpresaContextoMotorista(String(itemAlvo.empresa ?? ''));
    setLinhaContextoMotorista(
      String(
        itemAlvo.codigo_linha ?? itemAlvo.linha ?? itemAlvo.id_linha ?? '',
      ),
    );
    setMotoristaDialogMode('editar');
    setErroVinculo('');
    setVinculoSaving(false);
    setMotoristaFormKey((k) => k + 1);
    setMotoristaDialog(true);
    void carregarOcupacao();
  };

  const mensagemErroApi = (err: unknown, fallback: string): string => {
    if (err instanceof ApiRequestError) return err.message || fallback;
    if (err instanceof Error && err.message) return err.message;
    return fallback;
  };

  /** Persiste vínculo; sempre resolve com sucesso/erro — nunca deixa saving preso. */
  const gravarVinculo = async (idVeiculoNum: number): Promise<boolean> => {
    if (!mapa) {
      setErroVinculo('MAPA não carregado.');
      return false;
    }

    const chegadaApi = fromDateTimeLocal(chegada);
    const payload = {
      id_linha: Number(idLinhaForm),
      id_veiculo: idVeiculoNum,
      id_motorista: Number(idMotorista),
      hor_ini_jor: fromDateTimeLocal(horIni),
      hor_fim_jor: fromDateTimeLocal(horFim),
      chegada_ponto: chegadaApi,
      inicio_real: chegadaApi,
    };

    if (
      !Number.isFinite(payload.id_linha) ||
      payload.id_linha <= 0 ||
      !Number.isFinite(payload.id_veiculo) ||
      payload.id_veiculo <= 0 ||
      !Number.isFinite(payload.id_motorista) ||
      payload.id_motorista <= 0 ||
      !payload.hor_ini_jor ||
      !payload.hor_fim_jor ||
      !payload.chegada_ponto
    ) {
      setErroVinculo(
        'Preencha empresa, linha, veículo, motorista e os horários da jornada.',
      );
      return false;
    }

    try {
      if (motoristaDialogMode === 'novo') {
        const res = await createItem(mapa.id_registro, payload);
        toast.success('Motorista e veículo vinculados com sucesso.');
        setSelectedItemId(res.item.id_item);
      } else {
        if (editItemId == null) {
          setErroVinculo('Item inválido para edição.');
          return false;
        }
        await updateItem(editItemId, payload);
        toast.success('Motorista e veículo vinculados com sucesso.');
        setSelectedItemId(editItemId);
      }
      closeMotoristaDialog();
      await carregar();
      void carregarOcupacao();
      return true;
    } catch (err) {
      const msg = mensagemErroApi(
        err,
        'Não foi possível vincular motorista e veículo. Tente novamente.',
      );
      setErroVinculo(msg);
      toast.error(msg);
      return false;
    }
  };

  const onSalvarMotorista = async (e: FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!mapa) {
      setErroVinculo('MAPA não carregado.');
      return;
    }
    if (vinculoSaving) return;

    setErroVinculo('');

    if (!idEmpresaForm.trim()) {
      setErroVinculo('Selecione a empresa.');
      return;
    }
    if (!idLinhaForm.trim()) {
      setErroVinculo('Selecione a linha.');
      return;
    }

    let idVeiculoNum = Number(idVeiculoForm);

    if (motoristaDialogMode === 'novo') {
      const frota = frotaQuery.trim().toUpperCase();
      const erroFrota = validarFrotaParaEmpresa(frota, nomeEmpresaForm);
      if (erroFrota) {
        setFrotaErro(erroFrota);
        setErroVinculo(erroFrota);
        return;
      }
      if (motivoVeiculoOcupado) {
        setFrotaErro(motivoVeiculoOcupado);
        setErroVinculo(motivoVeiculoOcupado);
        return;
      }
      setFrotaErro('');

      const existente = buscarVeiculoPorFrota(frota);
      if (!existente) {
        setConfirmCriarVeiculo(true);
        return;
      }
      if (idsVeiculosOcupados.has(Number(existente.id_veiculo))) {
        const msg = `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`;
        setFrotaErro(msg);
        setErroVinculo(msg);
        return;
      }
      idVeiculoNum = Number(existente.id_veiculo);
      setIdVeiculoForm(String(existente.id_veiculo));
    } else if (!Number.isFinite(idVeiculoNum) || idVeiculoNum <= 0) {
      setErroVinculo('Veículo inválido.');
      return;
    }

    if (!idMotorista.trim()) {
      setErroVinculo('Selecione o motorista.');
      return;
    }
    if (idsMotoristasOcupados.has(Number(idMotorista))) {
      const mot = (cadastros?.motoristas ?? []).find(
        (m) => Number(m.id_motorista) === Number(idMotorista),
      );
      const rotulo = mot
        ? `${mot.matricula} — ${mot.nome}`
        : idMotorista;
      const msg = `O motorista ${rotulo} está em operação. Dê baixa antes de vinculá-lo novamente.`;
      setErroVinculo(msg);
      return;
    }
    if (!horIni.trim() || !horFim.trim() || !chegada.trim()) {
      setErroVinculo('Preencha chegada ao ponto, início e fim de jornada.');
      return;
    }
    if (!(chegada <= horIni && horIni < horFim)) {
      setErroVinculo('Horários inválidos: chegada ≤ início < fim.');
      return;
    }

    const veiculoDuplicado = (mapa.itens ?? []).some(
      (i) =>
        escalaEmAndamento(i) &&
        Number(i.id_veiculo) === idVeiculoNum &&
        (editItemId == null || i.id_item !== editItemId),
    );
    if (veiculoDuplicado) {
      setErroVinculo(
        `O veículo ${frotaQuery.trim().toUpperCase() || idVeiculoNum} está em operação. Dê baixa antes de vinculá-lo novamente.`,
      );
      return;
    }

    const motoristaDuplicado = (mapa.itens ?? []).some(
      (i) =>
        escalaEmAndamento(i) &&
        Number(i.id_motorista) === Number(idMotorista) &&
        (editItemId == null || i.id_item !== editItemId),
    );
    if (motoristaDuplicado) {
      const mot = (cadastros?.motoristas ?? []).find(
        (m) => Number(m.id_motorista) === Number(idMotorista),
      );
      const rotulo = mot
        ? `${mot.matricula} — ${mot.nome}`
        : idMotorista;
      setErroVinculo(
        `O motorista ${rotulo} está em operação. Dê baixa antes de vinculá-lo novamente.`,
      );
      return;
    }

    if (motoristaDialogMode === 'editar' && editItemId == null) {
      setErroVinculo('Item inválido para edição.');
      return;
    }

    setVinculoSaving(true);
    try {
      // Revalida ocupação imediatamente antes de criar (não segue se falhar).
      const ocup = await carregarOcupacao();
      if (!ocup.ok) {
        setErroVinculo(
          'Não foi possível verificar a disponibilidade de veículo e motorista. Verifique a conexão e tente novamente.',
        );
        return;
      }
      const veicOcup = ocup.veiculos.some((o) => {
        const idItem = Number(o.id_mapa_item ?? o.id_item);
        if (editItemId != null && idItem === Number(editItemId)) return false;
        return Number(o.id_veiculo) === idVeiculoNum;
      });
      if (veicOcup) {
        const frota = frotaQuery.trim().toUpperCase() || String(idVeiculoNum);
        setErroVinculo(
          `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`,
        );
        return;
      }
      const motOcup = ocup.motoristas.some((o) => {
        const idItem = Number(o.id_mapa_item ?? o.id_item);
        if (editItemId != null && idItem === Number(editItemId)) return false;
        return Number(o.id_motorista) === Number(idMotorista);
      });
      if (motOcup) {
        const mot = (cadastros?.motoristas ?? []).find(
          (m) => Number(m.id_motorista) === Number(idMotorista),
        );
        const rotulo = mot
          ? `${mot.matricula} — ${mot.nome}`
          : idMotorista;
        setErroVinculo(
          `O motorista ${rotulo} está em operação. Dê baixa antes de vinculá-lo novamente.`,
        );
        return;
      }
      await gravarVinculo(idVeiculoNum);
    } catch (err) {
      const msg = mensagemErroApi(
        err,
        'Não foi possível vincular motorista e veículo. Tente novamente.',
      );
      setErroVinculo(msg);
      toast.error(msg);
    } finally {
      setVinculoSaving(false);
    }
  };

  const confirmarCadastroVeiculo = async () => {
    if (!mapa || vinculoSaving) return;
    const frota = frotaQuery.trim().toUpperCase();
    const erroFrota = validarFrotaParaEmpresa(frota, nomeEmpresaForm);
    if (erroFrota) {
      setFrotaErro(erroFrota);
      setErroVinculo(erroFrota);
      setConfirmCriarVeiculo(false);
      return;
    }
    if (!idMotorista.trim()) {
      setErroVinculo('Selecione o motorista.');
      setConfirmCriarVeiculo(false);
      return;
    }
    if (!horIni.trim() || !horFim.trim() || !chegada.trim()) {
      setErroVinculo('Preencha chegada ao ponto, início e fim de jornada.');
      setConfirmCriarVeiculo(false);
      return;
    }
    if (!(chegada <= horIni && horIni < horFim)) {
      setErroVinculo('Horários inválidos: chegada ≤ início < fim.');
      setConfirmCriarVeiculo(false);
      return;
    }

    const motoristaDuplicado = (mapa.itens ?? []).some(
      (i) =>
        escalaEmAndamento(i) &&
        Number(i.id_motorista) === Number(idMotorista) &&
        (editItemId == null || i.id_item !== editItemId),
    );
    if (motoristaDuplicado) {
      const mot = (cadastros?.motoristas ?? []).find(
        (m) => Number(m.id_motorista) === Number(idMotorista),
      );
      const rotulo = mot
        ? `${mot.matricula} — ${mot.nome}`
        : idMotorista;
      setErroVinculo(
        `O motorista ${rotulo} está em operação. Dê baixa antes de vinculá-lo novamente.`,
      );
      setConfirmCriarVeiculo(false);
      return;
    }

    setVinculoSaving(true);
    setErroVinculo('');
    try {
      const res = await createVeiculo({
        numero_frota: frota,
        id_empresa: Number(idEmpresaForm),
      });
      const novo = res.veiculo;
      setIdVeiculoForm(String(novo.id_veiculo));
      setFrotaQuery(String(novo.numero_frota ?? frota));
      setConfirmCriarVeiculo(false);
      setCadastros((prev) =>
        prev ? { ...prev, veiculos: [...prev.veiculos, novo] } : prev,
      );

      const veiculoDuplicado = (mapa.itens ?? []).some(
        (i) =>
          escalaEmAndamento(i) &&
          Number(i.id_veiculo) === Number(novo.id_veiculo),
      );
      if (veiculoDuplicado) {
        setErroVinculo(
          `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`,
        );
        return;
      }

      const ocup = await carregarOcupacao();
      if (!ocup.ok) {
        setErroVinculo(
          'Não foi possível verificar a disponibilidade de veículo e motorista. Verifique a conexão e tente novamente.',
        );
        return;
      }
      const veicOcup = ocup.veiculos.some(
        (o) => Number(o.id_veiculo) === Number(novo.id_veiculo),
      );
      if (veicOcup) {
        setErroVinculo(
          `O veículo ${frota} está em operação. Dê baixa antes de vinculá-lo novamente.`,
        );
        return;
      }
      const motOcup = ocup.motoristas.some((o) => {
        const idItem = Number(o.id_mapa_item ?? o.id_item);
        if (editItemId != null && idItem === Number(editItemId)) return false;
        return Number(o.id_motorista) === Number(idMotorista);
      });
      if (motOcup) {
        const mot = (cadastros?.motoristas ?? []).find(
          (m) => Number(m.id_motorista) === Number(idMotorista),
        );
        const rotulo = mot
          ? `${mot.matricula} — ${mot.nome}`
          : idMotorista;
        setErroVinculo(
          `O motorista ${rotulo} está em operação. Dê baixa antes de vinculá-lo novamente.`,
        );
        return;
      }
      await gravarVinculo(Number(novo.id_veiculo));
    } catch (err) {
      setConfirmCriarVeiculo(false);
      const msg = mensagemErroApi(err, 'Falha ao cadastrar o veículo.');
      setErroVinculo(msg);
      toast.error(msg);
    } finally {
      setVinculoSaving(false);
    }
  };

  const onSalvarViagem = async (e: FormEvent) => {
    e.preventDefault();
    if (!mapa || !itemSelecionado || busy) return;
    setErroViagem('');
    if (!escalaEmAndamento(itemSelecionado)) {
      setErroViagem(
        'Escala encerrada. Crie uma nova escala para registrar novas viagens.',
      );
      return;
    }
    if (!itemProntoParaViagens) {
      setErroViagem(
        'Selecione um veículo e motorista para visualizar ou registrar viagens.',
      );
      return;
    }
    if (!saidaHora || !chegadaHora) {
      setErroViagem('Informe saída e chegada.');
      return;
    }
    if (conflitoViagemLocal) {
      setErroViagem(conflitoViagemLocal);
      return;
    }
    const dataMapa = toDateInput(mapa.data);
    const idMapaItem = Number(itemSelecionado.id_item);
    setBusy(true);
    try {
      await createViagem(idMapaItem, {
        id_mapa_item: idMapaItem,
        id_item: idMapaItem,
        horario_saida: combineDateAndTime(dataMapa, saidaHora),
        horario_chegada: combineDateAndTime(dataMapa, chegadaHora),
        qtd_pas_ida: Number(qtdIda) || 0,
        qtd_pas_volta: Number(qtdVolta) || 0,
      });
      toast.success('Viagem incluída.');
      setViagemDialog(false);
      setErroViagem('');
      await carregar();
    } catch (err) {
      const msg =
        err instanceof ApiRequestError
          ? err.message
          : 'Falha de comunicação com a API.';
      setErroViagem(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  const abrirDialogViagem = () => {
    setErroViagem('');
    setQtdIda('0');
    setQtdVolta('0');
    setChegadaHora('');
    if (saidaMinimaViagem) {
      setSaidaHora(saidaMinimaViagem);
    } else {
      setSaidaHora('');
    }
    setViagemDialog(true);
  };

  const confirmarExcluirMapa = async () => {
    if (!mapa) return;
    setConfirmDeleteMap(false);
    setBusy(true);
    try {
      await deleteMapa(mapa.id_registro);
      toast.success('MAPA excluído.');
      goLista();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirItem = async () => {
    if (selectedItemId == null) return;
    setConfirmDeleteItem(false);
    setBusy(true);
    try {
      await deleteItem(selectedItemId);
      toast.success('Carro excluído.');
      setSelectedItemId(null);
      await carregar();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarDarBaixa = async () => {
    if (!itemSelecionado || busy) return;
    if (!fimRealBaixa.trim()) {
      toast.error('Informe a data e hora real de baixa.');
      return;
    }
    const idItem = itemSelecionado.id_item;
    const fimReal = fromDateTimeLocal(fimRealBaixa);
    setConfirmBaixaItem(false);
    setBusy(true);
    try {
      const res = await darBaixaItem(idItem, { fim_real: fimReal });
      setMapa((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          itens: prev.itens.map((i) =>
            i.id_item === idItem
              ? {
                  ...i,
                  ...res.item,
                  viagens: i.viagens,
                }
              : i,
          ),
        };
      });
      const trabalhado =
        res.item?.duracao_trabalhada_hhmm ??
        formatDuracaoHhMm(res.item?.duracao_trabalhada_minutos);
      toast.success(
        trabalhado && trabalhado !== '—'
          ? `Baixa registrada. Trabalhado: ${trabalhado}.`
          : 'Baixa registrada. Veículo e motorista liberados.',
      );
      void carregarOcupacao();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirViagem = async () => {
    if (confirmDeleteViagem == null) return;
    const id = confirmDeleteViagem;
    setConfirmDeleteViagem(null);
    setBusy(true);
    try {
      await deleteViagem(id);
      toast.success('Viagem excluída.');
      await carregar();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <AppShell className="bg-screen">
        <div className="page min-h-dvh bg-screen text-slate-900">
          <PageHeader title="MAPA" onBack={goLista} />
          <LoadingState label="Carregando MAPA…" className="min-h-[40vh]" />
        </div>
      </AppShell>
    );
  }

  if (!mapa) {
    return (
      <AppShell className="bg-screen">
        <div className="page min-h-dvh bg-screen text-slate-900">
          <PageHeader title="MAPA" onBack={goLista} />
          <EmptyState
            title="MAPA não encontrado"
            description="Volte à lista e tente novamente."
            className="min-h-[40vh]"
          />
        </div>
      </AppShell>
    );
  }

  const isEditar = motoristaDialogMode === 'editar';

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader
          title="MAPA"
          onBack={goLista}
          rightSlot={
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Editar MAPA"
              onClick={() => navigate(`/mapas/${idRegistro}/editar`)}
              className="h-11 w-11 min-h-[44px] min-w-[44px] rounded border border-white/70 text-white hover:bg-white/10"
            >
              <Pencil className="h-5 w-5" strokeWidth={2.25} />
            </Button>
          }
        />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-4">
          <section className="rounded-xl border border-slate-400/40 bg-white/50 p-4">
            <div className="mb-2">
              <p className="text-lg font-bold text-primary">
                Nº {formatCodigoMapa(mapa.codigo_mapa)}
              </p>
              <p className="text-sm text-muted-foreground">
                {toDateInput(mapa.data)} · {mapa.turno}
              </p>
              <p className="text-xs text-muted-foreground">
                Desp.: {mapa.despachante} · {formatHora(mapa.inicio_jornada_des)}–
                {formatHora(mapa.fim_jornada_des)}
              </p>
            </div>
          </section>

          <section aria-labelledby="mapa-carros-heading">
            <div className="mb-2 flex items-center justify-between gap-2">
              <h2
                id="mapa-carros-heading"
                className="text-[13px] font-bold uppercase tracking-wide text-muted-foreground"
              >
                Carros
              </h2>
              <div className="flex flex-wrap items-center justify-end gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-11 min-h-[44px] rounded-full px-3 text-xs font-bold uppercase"
                  aria-label="Dar baixa"
                  disabled={!itemPodeDarBaixa || busy}
                  onClick={abrirDialogBaixa}
                >
                  Dar baixa
                </Button>
                <Button
                  type="button"
                  size="icon"
                  className="h-11 w-11 min-h-[44px] min-w-[44px] rounded-full"
                  aria-label="Vincular motorista"
                  onClick={() => openMotoristaNovo()}
                >
                  <UserPlus className="h-5 w-5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  className="h-11 w-11 min-h-[44px] min-w-[44px] rounded-full"
                  aria-label="Excluir carro"
                  disabled={selectedItemId == null}
                  onClick={() => setConfirmDeleteItem(true)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {mapa.itens.length === 0 ? (
              <EmptyState
                title="Nenhum veículo neste MAPA"
                description="Use o botão de vincular motorista para incluir a primeira escala."
                className="rounded-xl border border-dashed border-slate-400/50 bg-white/40 py-10"
              />
            ) : (
              <>
                {/* Mobile: cards clicáveis */}
                <ul
                  className="flex flex-col gap-2 md:hidden"
                  role="listbox"
                  aria-label="Escalas do MAPA"
                  aria-activedescendant={
                    selectedItemId != null
                      ? `escala-card-${selectedItemId}`
                      : undefined
                  }
                >
                  {mapa.itens.map((item) => {
                    const selected = item.id_item === selectedItemId;
                    const temVinculo =
                      item.id_motorista != null && Number(item.id_motorista) > 0;
                    const emAndamento = escalaEmAndamento(item);
                    return (
                      <li key={item.id_item}>
                        <div
                          id={`escala-card-${item.id_item}`}
                          role="option"
                          aria-selected={selected}
                          tabIndex={0}
                          className={cn(
                            'w-full rounded-xl border bg-white/80 p-3 text-left shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                            selected
                              ? 'border-primary bg-primary/10 ring-2 ring-primary/40'
                              : 'border-slate-400/40 hover:border-slate-500/60',
                          )}
                          onClick={() => setSelectedItemId(item.id_item)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              setSelectedItemId(item.id_item);
                            }
                          }}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1 space-y-1.5">
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="text-base font-bold text-slate-900">
                                  {frotaItemLabel(item)}
                                </p>
                                <StatusEscalaBadge item={item} />
                              </div>
                              <p className="text-sm text-slate-700">
                                <span className="font-semibold">Empresa:</span>{' '}
                                {item.empresa ?? '—'}
                              </p>
                              <p className="text-sm text-slate-700">
                                <span className="font-semibold">Linha:</span>{' '}
                                {linhaItemLabel(item)}
                              </p>
                              <p className="text-sm text-slate-700">
                                <span className="font-semibold">Motorista:</span>{' '}
                                {motoristaItemLabel(item)}
                              </p>
                              <p className="text-sm text-slate-700">
                                <span className="font-semibold">Jornada:</span>{' '}
                                {jornadaItemLabel(item)}
                              </p>
                            </div>
                            <Button
                              type="button"
                              size="icon"
                              variant="ghost"
                              className="h-11 w-11 min-h-[44px] min-w-[44px] shrink-0"
                              aria-label="Editar vínculo"
                              disabled={!temVinculo || !emAndamento}
                              onClick={(e) => {
                                e.stopPropagation();
                                openMotoristaEditar(item.id_item);
                              }}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>

                {/* Desktop: tabela */}
                <div className="hidden overflow-hidden rounded-xl border border-slate-400/40 md:block">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                        <TableHead className="text-[11px] leading-tight">Carro</TableHead>
                        <TableHead className="text-[11px] leading-tight">Status</TableHead>
                        <TableHead className="text-[11px] leading-tight">Empresa</TableHead>
                        <TableHead className="text-[11px] leading-tight">Linha</TableHead>
                        <TableHead className="text-[11px] leading-tight">Matrícula</TableHead>
                        <TableHead className="text-[11px] leading-tight">Início</TableHead>
                        <TableHead className="text-[11px] leading-tight">Chegada</TableHead>
                        <TableHead className="w-12 p-0" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mapa.itens.map((item, i) => {
                        const temVinculo =
                          item.id_motorista != null && Number(item.id_motorista) > 0;
                        const emAndamento = escalaEmAndamento(item);
                        const selected = item.id_item === selectedItemId;
                        return (
                          <TableRow
                            key={item.id_item}
                            tabIndex={0}
                            aria-selected={selected}
                            className={cn(
                              'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                              selected
                                ? 'bg-primary/10'
                                : i % 2 === 0
                                  ? 'bg-white'
                                  : 'bg-[hsl(var(--zebra))]',
                            )}
                            onClick={() => setSelectedItemId(item.id_item)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                setSelectedItemId(item.id_item);
                              }
                            }}
                          >
                            <TableCell className="text-xs font-medium">
                              {frotaItemLabel(item)}
                            </TableCell>
                            <TableCell className="text-xs">
                              <StatusEscalaBadge item={item} />
                            </TableCell>
                            <TableCell className="text-xs">
                              {item.empresa ?? '—'}
                            </TableCell>
                            <TableCell className="text-xs">
                              {linhaItemLabel(item)}
                            </TableCell>
                            <TableCell className="text-xs">
                              {item.matricula_motorista ?? '—'}
                            </TableCell>
                            <TableCell className="text-xs">
                              {formatHora(item.hor_ini_jor)}
                            </TableCell>
                            <TableCell className="text-xs">
                              {formatHora(item.chegada_ponto)}
                            </TableCell>
                            <TableCell className="p-1 text-right">
                              <Button
                                type="button"
                                size="icon"
                                variant="ghost"
                                className="h-11 w-11 min-h-[44px] min-w-[44px]"
                                aria-label="Editar vínculo"
                                disabled={!temVinculo || !emAndamento}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openMotoristaEditar(item.id_item);
                                }}
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </>
            )}
          </section>

          <Separator />

          <section aria-labelledby="mapa-viagens-heading">
            <div className="mb-2 flex items-center justify-between gap-2">
              <h2
                id="mapa-viagens-heading"
                className="text-[13px] font-bold uppercase tracking-wide text-muted-foreground"
              >
                {resumoViagens
                  ? `Viagens — ${resumoViagens.frota}`
                  : 'Viagens'}
              </h2>
              <Button
                type="button"
                size="icon"
                className="h-11 w-11 min-h-[44px] min-w-[44px] shrink-0 rounded-full"
                aria-label="Nova viagem"
                title={
                  itemSelecionado && !escalaEmAndamento(itemSelecionado)
                    ? 'Escala encerrada. Crie uma nova escala para registrar novas viagens.'
                    : 'Nova viagem'
                }
                disabled={!itemProntoParaViagens}
                onClick={abrirDialogViagem}
              >
                <Plus className="h-5 w-5" />
              </Button>
            </div>

            {resumoViagens ? (
              <div
                className="mb-3 rounded-xl border border-slate-400/40 bg-white/70 p-3 shadow-sm"
                aria-live="polite"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-bold text-slate-900">
                    Veículo {resumoViagens.frota}
                  </p>
                  <Badge
                    variant={resumoViagens.encerrada ? 'secondary' : 'default'}
                    className="text-[10px] uppercase"
                  >
                    {resumoViagens.statusLabel}
                  </Badge>
                </div>
                <dl className="mt-2 grid gap-1.5 text-sm text-slate-800 sm:grid-cols-2">
                  <div>
                    <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                      Motorista
                    </dt>
                    <dd>{resumoViagens.motoristaTxt}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                      Linha
                    </dt>
                    <dd>{resumoViagens.linhaTxt}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                      Empresa
                    </dt>
                    <dd>{resumoViagens.empresaTxt}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] font-semibold uppercase text-muted-foreground">
                      Status
                    </dt>
                    <dd>{resumoViagens.statusLabel}</dd>
                  </div>
                </dl>
                {resumoViagens.jornadaTxt ? (
                  <p className="mt-2 text-xs text-slate-700">
                    Jornada {resumoViagens.jornadaTxt}
                  </p>
                ) : null}
                {resumoViagens.encerrada ? (
                  <p className="mt-1 text-xs text-slate-700">
                    Real {resumoViagens.inicioRealTxt}–
                    {resumoViagens.fimRealTxt}
                    {resumoViagens.trabalhadoTxt &&
                    resumoViagens.trabalhadoTxt !== '—'
                      ? ` · Trabalhado: ${resumoViagens.trabalhadoTxt}`
                      : ''}
                  </p>
                ) : null}
              </div>
            ) : null}

            {!itemSelecionado ? (
              <EmptyState
                title="Nenhuma escala selecionada"
                description="Selecione uma escala para visualizar ou registrar viagens."
                className="rounded-xl border border-dashed border-slate-400/50 bg-white/40 py-10"
              />
            ) : !escalaEmAndamento(itemSelecionado) ? (
              <>
                <p className="mb-2 rounded-xl border border-dashed border-slate-400/50 bg-white/40 px-4 py-3 text-center text-sm text-slate-700">
                  Esta escala foi encerrada. Crie uma nova escala para registrar
                  novas viagens.
                </p>
                <div className="overflow-x-auto overflow-hidden rounded-xl border border-slate-400/40">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                        <TableHead className="text-[11px]">Saída</TableHead>
                        <TableHead className="text-[11px]">Chegada</TableHead>
                        <TableHead className="text-[11px]">Qtd ida</TableHead>
                        <TableHead className="text-[11px]">Qtd volta</TableHead>
                        <TableHead className="w-12 p-0" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {viagensDoItem.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="py-6 text-muted-foreground">
                            Nenhuma viagem.
                          </TableCell>
                        </TableRow>
                      ) : (
                        viagensDoItem.map((v, i) => (
                          <TableRow
                            key={v.id_viagem}
                            className={i % 2 === 0 ? 'bg-white' : 'bg-[hsl(var(--zebra))]'}
                          >
                            <TableCell className="text-xs">{formatHora(v.horario_saida)}</TableCell>
                            <TableCell className="text-xs">{formatHora(v.horario_chegada)}</TableCell>
                            <TableCell className="text-xs">{v.qtd_pas_ida}</TableCell>
                            <TableCell className="text-xs">{v.qtd_pas_volta}</TableCell>
                            <TableCell className="p-1" />
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </>
            ) : !itemProntoParaViagens ? (
              <EmptyState
                title="Motorista não vinculado"
                description="Este carro ainda não tem motorista vinculado. Use o lápis ou Incluir vínculo antes de registrar viagens."
                className="rounded-xl border border-dashed border-slate-400/50 bg-white/40 py-10"
              />
            ) : viagensDoItem.length === 0 ? (
              <EmptyState
                title="Nenhuma viagem"
                description="Toque em + para registrar a primeira viagem desta escala."
                className="rounded-xl border border-dashed border-slate-400/50 bg-white/40 py-10"
              />
            ) : (
              <div className="overflow-x-auto overflow-hidden rounded-xl border border-slate-400/40">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                      <TableHead className="text-[11px]">Saída</TableHead>
                      <TableHead className="text-[11px]">Chegada</TableHead>
                      <TableHead className="text-[11px]">Qtd ida</TableHead>
                      <TableHead className="text-[11px]">Qtd volta</TableHead>
                      <TableHead className="w-12 p-0" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {viagensDoItem.map((v, i) => (
                      <TableRow
                        key={v.id_viagem}
                        className={i % 2 === 0 ? 'bg-white' : 'bg-[hsl(var(--zebra))]'}
                      >
                        <TableCell className="text-xs">{formatHora(v.horario_saida)}</TableCell>
                        <TableCell className="text-xs">{formatHora(v.horario_chegada)}</TableCell>
                        <TableCell className="text-xs">{v.qtd_pas_ida}</TableCell>
                        <TableCell className="text-xs">{v.qtd_pas_volta}</TableCell>
                        <TableCell className="p-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-11 w-11 min-h-[44px] min-w-[44px] text-destructive"
                            aria-label="Excluir viagem"
                            onClick={() => setConfirmDeleteViagem(v.id_viagem)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>

          <Button
            type="button"
            variant="outline"
            className="mt-auto w-full"
            disabled={busy}
            onClick={() => setConfirmDeleteMap(true)}
          >
            Excluir MAPA
          </Button>
        </div>

        <Dialog
          open={motoristaDialog}
          onOpenChange={(open) => {
            if (!open) closeMotoristaDialog();
          }}
        >
          <DialogContent className="max-w-[min(100%,22rem)] border-slate-400/50 bg-card p-4 sm:p-5">
            <DialogClose
              type="button"
              className="absolute right-2 top-2 z-10 flex h-11 w-11 min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Fechar"
            >
              <X className="h-5 w-5" strokeWidth={2.25} />
            </DialogClose>
            <DialogHeader className="shrink-0 pr-10">
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide text-slate-900">
                {motoristaDialogMode === 'editar'
                  ? 'Editar vínculo'
                  : 'Vincular motorista'}
              </DialogTitle>
            </DialogHeader>
            <form
              key={motoristaFormKey}
              className="mt-3 flex min-h-0 flex-1 flex-col"
              onSubmit={(e) => void onSalvarMotorista(e)}
            >
              <div className="field-stack min-h-0 flex-1 gap-3 overflow-y-auto overscroll-contain pe-0.5">
              {ocupacaoLoading ? (
                <p className="rounded-md border border-slate-300/70 bg-slate-50 px-3 py-2 text-sm text-slate-700" role="status">
                  Verificando disponibilidade...
                </p>
              ) : null}
              {ocupacaoErro ? (
                <div className="space-y-2 rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2">
                  <p className="text-sm text-destructive" role="alert">
                    Não foi possível verificar a disponibilidade de veículo e
                    motorista. Verifique a conexão e tente novamente.
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="min-h-[44px]"
                    disabled={ocupacaoLoading || vinculoSaving}
                    onClick={() => void carregarOcupacao()}
                  >
                    Tentar novamente
                  </Button>
                </div>
              ) : null}
              {erroVinculo ? (
                <p className="text-sm text-destructive" role="alert">
                  {erroVinculo}
                </p>
              ) : null}

              <section
                className="space-y-3 rounded-lg border border-slate-300/60 bg-white/70 p-3"
                aria-labelledby="vinculo-bloco-escala"
              >
                <h3
                  id="vinculo-bloco-escala"
                  className="text-[12px] font-bold uppercase tracking-wide text-muted-foreground"
                >
                  Escala
                </h3>
                {isEditar ? (
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>
                      Empresa:{' '}
                      <span className="font-semibold text-slate-900">
                        {empresaContextoMotorista || '—'}
                      </span>
                    </p>
                    <p>
                      Linha:{' '}
                      <span className="font-semibold text-slate-900">
                        {linhaContextoMotorista || '—'}
                      </span>
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="flex w-full flex-col gap-1">
                      <Label className="text-[13px] font-semibold uppercase text-slate-900">
                        Empresa <span className="req">*</span>
                      </Label>
                      <Select
                        value={idEmpresaForm ?? ''}
                        onValueChange={(v) => {
                          setIdEmpresaForm(v ?? '');
                          limparLinhaEAbaixo();
                        }}
                      >
                        <SelectTrigger className="h-11 min-h-[44px] bg-white text-base">
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent position="popper" className="z-[400]">
                          {empresas.length === 0 ? (
                            <SelectItem value="__empty_empresa" disabled>
                              Nenhuma empresa cadastrada
                            </SelectItem>
                          ) : (
                            empresas.map((e) => (
                              <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>
                                {e.descricao}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex w-full flex-col gap-1">
                      <Label className="text-[13px] font-semibold uppercase text-slate-900">
                        Linha <span className="req">*</span>
                      </Label>
                      <Select
                        value={idLinhaForm ?? ''}
                        onValueChange={(v) => {
                          setIdLinhaForm(v ?? '');
                          limparVeiculoEAbaixo();
                        }}
                        disabled={!idEmpresaForm}
                      >
                        <SelectTrigger className="h-11 min-h-[44px] bg-white text-base">
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent position="popper" className="z-[400]">
                          {linhasFiltradas.length === 0 ? (
                            <SelectItem value="__empty_linha" disabled>
                              Nenhuma linha para esta empresa
                            </SelectItem>
                          ) : (
                            linhasFiltradas.map((l) => (
                              <SelectItem key={l.id_linha} value={String(l.id_linha)}>
                                {l.codigo_linha != null
                                  ? `${l.codigo_linha} — ${l.descricao}`
                                  : l.descricao}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </section>

              <section
                className="space-y-3 rounded-lg border border-slate-300/60 bg-white/70 p-3"
                aria-labelledby="vinculo-bloco-veiculo"
              >
                <h3
                  id="vinculo-bloco-veiculo"
                  className="text-[12px] font-bold uppercase tracking-wide text-muted-foreground"
                >
                  Veículo e motorista
                </h3>
                {isEditar ? (
                  <p className="text-sm text-muted-foreground">
                    Veículo:{' '}
                    <span className="font-semibold text-slate-900">
                      {frotaContextoMotorista || '—'}
                    </span>
                  </p>
                ) : (
                  <div className="flex w-full flex-col gap-1">
                    <Label
                      htmlFor="veiculo-frota"
                      className="text-[13px] font-semibold uppercase text-slate-900"
                    >
                      Veículo <span className="req">*</span>
                    </Label>
                    <Input
                      id="veiculo-frota"
                      ref={veiculoInputRef}
                      className="h-11 min-h-[44px] rounded-lg border-slate-400 bg-white font-mono text-base uppercase tracking-wide text-slate-900"
                      placeholder={
                        idEmpresaForm && idLinhaForm
                          ? placeholderFrotaEmpresa(nomeEmpresaForm)
                          : 'Selecione empresa e linha antes'
                      }
                      value={frotaQuery}
                      disabled={!idEmpresaForm || !idLinhaForm}
                      autoComplete="off"
                      maxLength={6}
                      inputMode="text"
                      spellCheck={false}
                      aria-invalid={Boolean(frotaErro)}
                      aria-describedby={
                        frotaErro
                          ? 'veiculo-frota-erro'
                          : idEmpresaForm && idLinhaForm
                            ? 'veiculo-frota-mascara'
                            : undefined
                      }
                      onChange={(e) => onFrotaQueryChange(e.target.value)}
                    />
                    {idEmpresaForm && idLinhaForm && !frotaErro ? (
                      <span
                        id="veiculo-frota-mascara"
                        className="font-mono text-[12px] tracking-widest text-slate-500"
                      >
                        {mascaraGuiaFrotaEmpresa(nomeEmpresaForm)}
                      </span>
                    ) : null}
                    {frotaErro || motivoVeiculoOcupado ? (
                      <span
                        id="veiculo-frota-erro"
                        className="text-[13px] text-destructive"
                        role="alert"
                      >
                        {frotaErro || motivoVeiculoOcupado}
                      </span>
                    ) : null}
                  </div>
                )}

                <div className="flex w-full flex-col gap-1">
                  <Label className="text-[13px] font-semibold uppercase text-slate-900">
                    Motorista <span className="req">*</span>
                  </Label>
                  <Select
                    value={idMotorista ?? ''}
                    onValueChange={(v) => {
                      setIdMotorista(v ?? '');
                      limparHorariosMotorista();
                    }}
                    disabled={
                      motoristaDialogMode === 'novo' ? !frotaValida : !idVeiculoForm
                    }
                  >
                    <SelectTrigger className="h-11 min-h-[44px] bg-white text-base">
                      <SelectValue
                        placeholder={
                          motoristaDialogMode === 'novo'
                            ? frotaValida
                              ? 'Selecione'
                              : 'Informe o veículo antes'
                            : idVeiculoForm
                              ? 'Selecione'
                              : 'Selecione o veículo antes'
                        }
                      />
                    </SelectTrigger>
                    <SelectContent position="popper" className="z-[400]">
                      {motoristas.length === 0 ? (
                        <SelectItem value="__empty_motorista" disabled>
                          Nenhum motorista disponível
                        </SelectItem>
                      ) : (
                        motoristas.map((m) => (
                          <SelectItem
                            key={m.id_motorista}
                            value={String(m.id_motorista)}
                            disabled={Boolean(m.emOperacao)}
                          >
                            {m.matricula} — {m.nome}
                            {m.emOperacao ? ' (Em operação)' : ''}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </section>

              <section
                className="space-y-3 rounded-lg border border-slate-300/60 bg-white/70 p-3"
                aria-labelledby="vinculo-bloco-horarios"
              >
                <h3
                  id="vinculo-bloco-horarios"
                  className="text-[12px] font-bold uppercase tracking-wide text-muted-foreground"
                >
                  Horários
                </h3>
                <FormField
                  label="Chegada ao ponto"
                  requiredMark
                  type="datetime-local"
                  value={chegada ?? ''}
                  onChange={(e) => setChegada(e.target.value)}
                  disabled={!idMotorista}
                  className="h-11 min-h-[44px]"
                />
                <FormField
                  label="Início jornada"
                  requiredMark
                  type="datetime-local"
                  value={horIni ?? ''}
                  onChange={(e) => setHorIni(e.target.value)}
                  disabled={!idMotorista}
                  className="h-11 min-h-[44px]"
                />
                <FormField
                  label="Fim jornada"
                  requiredMark
                  type="datetime-local"
                  value={horFim ?? ''}
                  onChange={(e) => setHorFim(e.target.value)}
                  disabled={!idMotorista}
                  className="h-11 min-h-[44px]"
                />
              </section>
              </div>

              <DialogFooter className="mt-4 shrink-0 grid grid-cols-2 gap-3">
                <Button
                  type="submit"
                  className="min-h-[44px]"
                  disabled={
                    vinculoSaving ||
                    (motoristaDialogMode === 'novo' &&
                      (!frotaValida || Boolean(motivoVeiculoOcupado)))
                  }
                >
                  {vinculoSaving
                    ? 'SALVANDO...'
                    : ocupacaoLoading
                      ? 'Verificando...'
                      : 'Confirmar'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="min-h-[44px]"
                  disabled={vinculoSaving}
                  onClick={closeMotoristaDialog}
                >
                  Cancelar
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        <Dialog
          open={viagemDialog}
          onOpenChange={(open) => {
            setViagemDialog(open);
            if (!open) setErroViagem('');
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova viagem</DialogTitle>
            </DialogHeader>
            <form className="field-stack" onSubmit={(e) => void onSalvarViagem(e)}>
              {ultimaViagemItem && saidaMinimaViagem ? (
                <p className="rounded-md border border-slate-300/70 bg-slate-50 px-3 py-2 text-sm text-slate-800">
                  Última viagem: {formatHora(ultimaViagemItem.horario_saida)}–
                  {formatHora(ultimaViagemItem.horario_chegada)}. Próxima saída
                  permitida: {saidaMinimaViagem}.
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Primeira viagem desta escala.
                </p>
              )}
              {erroViagem ? (
                <p className="text-sm text-destructive" role="alert">
                  {erroViagem}
                </p>
              ) : conflitoViagemLocal ? (
                <p className="text-sm text-destructive" role="alert">
                  {conflitoViagemLocal}
                </p>
              ) : null}
              <FormField
                label="Saída"
                requiredMark
                type="time"
                value={saidaHora}
                onChange={(e) => {
                  setSaidaHora(e.target.value);
                  setErroViagem('');
                }}
              />
              <FormField
                label="Chegada"
                requiredMark
                type="time"
                value={chegadaHora}
                onChange={(e) => {
                  setChegadaHora(e.target.value);
                  setErroViagem('');
                }}
              />
              <FormField
                label="Qtd ida"
                type="number"
                min={0}
                value={qtdIda}
                onChange={(e) => setQtdIda(e.target.value)}
              />
              <FormField
                label="Qtd volta"
                type="number"
                min={0}
                value={qtdVolta}
                onChange={(e) => setQtdVolta(e.target.value)}
              />
              <DialogFooter className="grid grid-cols-2 gap-3">
                <Button
                  type="submit"
                  disabled={
                    busy ||
                    !itemProntoParaViagens ||
                    !saidaHora ||
                    !chegadaHora ||
                    Boolean(conflitoViagemLocal)
                  }
                >
                  Confirmar
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() => setViagemDialog(false)}
                >
                  Cancelar
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        <ConfirmDialog
          open={confirmCriarVeiculo}
          title="Cadastrar veículo"
          message={`Veículo ${frotaQuery.trim().toUpperCase() || '—'} não encontrado para ${nomeEmpresaForm || 'a empresa'}. Deseja cadastrá-lo?`}
          confirmLabel="Cadastrar"
          cancelLabel="Cancelar"
          onConfirm={() => void confirmarCadastroVeiculo()}
          onCancel={() => setConfirmCriarVeiculo(false)}
        />

        <ConfirmDialog
          open={confirmDeleteMap}
          title="Excluir MAPA"
          message="Exclui o MAPA, carros e viagens. Continuar?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirMapa()}
          onCancel={() => setConfirmDeleteMap(false)}
        />

        <ConfirmDialog
          open={confirmDeleteItem}
          title="Excluir carro"
          message="Exclui o carro e suas viagens. Continuar?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirItem()}
          onCancel={() => setConfirmDeleteItem(false)}
        />

        <Dialog
          open={confirmBaixaItem}
          onOpenChange={(open) => {
            if (!open) setConfirmBaixaItem(false);
          }}
        >
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Dar baixa</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 text-sm">
              <p>
                {itemSelecionado
                  ? `Encerrar escala do veículo ${String(itemSelecionado.numero_frota ?? itemSelecionado.id_veiculo)} · motorista ${[itemSelecionado.matricula_motorista, itemSelecionado.motorista].filter(Boolean).join(' — ') || '—'}.`
                  : 'Encerrar esta escala.'}
              </p>
              <p>
                Início real:{' '}
                <span className="font-semibold">{previewBaixa.inicioHora}</span>
              </p>
              <FormField
                label="Data e hora real de baixa *"
                type="datetime-local"
                value={fimRealBaixa}
                onChange={(e) => setFimRealBaixa(e.target.value)}
                required
              />
              <p className="rounded-md border border-slate-300/70 bg-slate-50 px-3 py-2 text-slate-800">
                As horas de {previewBaixa.inicioHora} até {previewBaixa.fimHora}{' '}
                serão registradas no banco de horas do motorista.
                {previewBaixa.minutos != null ? (
                  <>
                    {' '}
                    Prévia: <strong>{previewBaixa.duracao}</strong> (
                    {previewBaixa.minutos} min).
                  </>
                ) : null}
              </p>
            </div>
            <DialogFooter className="grid grid-cols-2 gap-3">
              <Button
                type="button"
                disabled={busy || !fimRealBaixa.trim()}
                onClick={() => void confirmarDarBaixa()}
              >
                Dar baixa
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => setConfirmBaixaItem(false)}
              >
                Cancelar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <ConfirmDialog
          open={confirmDeleteViagem != null}
          title="Excluir viagem"
          message="Confirma a exclusão desta viagem?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirViagem()}
          onCancel={() => setConfirmDeleteViagem(null)}
        />
      </div>
    </AppShell>
  );
}
