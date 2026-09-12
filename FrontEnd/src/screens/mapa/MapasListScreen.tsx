import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { MapPinned, Plus, Search, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { ApiRequestError } from '@/api/client';
import { deleteTodosMapas, listMapas } from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { OpsPageHeader } from '@/components/ops';
import {
  FilterBottomSheet,
  FilterChipsBar,
  OpsCard,
} from '@/components/ops';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EmpresaChip, Pill } from '@/components/ui/pill';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaListaItem } from '@/types/mapa';
import { formatCodigoMapa, toDateBR } from '@/utils/mapaFormat';
import { SCREEN_BG } from '@/theme/tokens';

const BG = SCREEN_BG;
const FILTRO_TODOS = '__todos__';

function textoBusca(row: MapaListaItem): string {
  return [
    formatCodigoMapa(row.codigo_mapa),
    String(row.codigo_mapa ?? ''),
    row.empresa ?? '',
    row.linha ?? '',
    row.turno ?? '',
  ]
    .join(' ')
    .toLowerCase();
}

function dataExibicao(row: MapaListaItem): string | null {
  const raw = row.data;
  if (raw == null || String(raw).trim() === '') return null;
  const br = toDateBR(String(raw));
  return br || null;
}

function statusMapaLista(row: MapaListaItem): {
  label: string;
  tone: 'ok' | 'info' | 'neutral';
} {
  const qtd = Number(row.total_viagens ?? row.qtd_viagens ?? NaN);
  if (Number.isFinite(qtd) && qtd > 0) {
    return { label: 'Com viagens', tone: 'ok' };
  }
  if (row.linha) return { label: 'Planejado', tone: 'info' };
  return { label: 'Cadastrado', tone: 'neutral' };
}

function qtdViagensLabel(row: MapaListaItem): string {
  const qtd = row.total_viagens ?? row.qtd_viagens;
  if (qtd == null || !Number.isFinite(Number(qtd))) return 'Viagens no detalhe';
  const n = Number(qtd);
  return `${n} viagem${n === 1 ? '' : 's'}`;
}

/** Lista MAPA — card sem Excluir (exclusão só no detalhe). */
export function MapasListScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  useScreenBg(BG);

  const [mapas, setMapas] = useState<MapaListaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busca, setBusca] = useState('');
  const [filtroTurno, setFiltroTurno] = useState('');
  const [filtroLinha, setFiltroLinha] = useState('');
  const [filtroOpen, setFiltroOpen] = useState(false);
  const [draftTurno, setDraftTurno] = useState('');
  const [draftLinha, setDraftLinha] = useState('');
  const [draftBusca, setDraftBusca] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);

  const aliveRef = useRef(true);

  const carregar = useCallback(async () => {
    if (!aliveRef.current) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listMapas();
      if (!aliveRef.current) return;
      setMapas(data.mapas);
    } catch (e) {
      if (!aliveRef.current) return;
      setMapas([]);
      setError(
        e instanceof ApiRequestError
          ? e.message
          : 'Não foi possível conectar à API.',
      );
    } finally {
      if (aliveRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    aliveRef.current = true;
    void carregar();
    return () => {
      aliveRef.current = false;
    };
  }, [carregar, location.key]);

  useEffect(() => {
    const onFocus = () => {
      if (!aliveRef.current) return;
      void carregar();
    };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') onFocus();
    };
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [carregar]);

  const turnosOpcoes = useMemo(() => {
    const set = new Set<string>();
    for (const m of mapas) {
      const t = String(m.turno ?? '').trim();
      if (t) set.add(t);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'pt-BR'));
  }, [mapas]);

  const linhasOpcoes = useMemo(() => {
    const set = new Set<string>();
    for (const m of mapas) {
      const l = String(m.linha ?? '').trim();
      if (l) set.add(l);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'pt-BR'));
  }, [mapas]);

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return mapas.filter((row) => {
      if (filtroTurno && String(row.turno ?? '').trim() !== filtroTurno) {
        return false;
      }
      if (filtroLinha) {
        const linha = String(row.linha ?? '').trim();
        if (linha !== filtroLinha) return false;
      }
      if (q && !textoBusca(row).includes(q)) return false;
      return true;
    });
  }, [mapas, busca, filtroTurno, filtroLinha]);

  const temFiltroAtivo =
    busca.trim() !== '' || filtroTurno !== '' || filtroLinha !== '';

  const limparFiltros = () => {
    setBusca('');
    setFiltroTurno('');
    setFiltroLinha('');
    setDraftBusca('');
    setDraftTurno('');
    setDraftLinha('');
  };

  const abrirFiltro = () => {
    setDraftBusca(busca);
    setDraftTurno(filtroTurno);
    setDraftLinha(filtroLinha);
    setFiltroOpen(true);
  };

  const aplicarFiltro = () => {
    setBusca(draftBusca);
    setFiltroTurno(draftTurno);
    setFiltroLinha(draftLinha);
    setFiltroOpen(false);
  };

  const chips = useMemo(() => {
    const list: { id: string; label: string; onClear: () => void }[] = [];
    if (busca.trim()) {
      list.push({
        id: 'busca',
        label: `Busca: ${busca.trim()}`,
        onClear: () => setBusca(''),
      });
    }
    if (filtroTurno) {
      list.push({
        id: 'turno',
        label: `Turno: ${filtroTurno}`,
        onClear: () => setFiltroTurno(''),
      });
    }
    if (filtroLinha) {
      list.push({
        id: 'linha',
        label: `Linha: ${filtroLinha}`,
        onClear: () => setFiltroLinha(''),
      });
    }
    return list;
  }, [busca, filtroTurno, filtroLinha]);

  const abrirMapa = (id: number) => {
    navigate(`/mapas/${id}`);
  };

  const novoMapa = () => navigate('/mapas/novo');

  const confirmarExcluirTodos = async () => {
    if (busy || mapas.length === 0) return;
    setConfirmDeleteAll(false);
    setBusy(true);
    try {
      const res = await deleteTodosMapas();
      if (!aliveRef.current) return;
      const n = Number(res.excluidos ?? mapas.length);
      toast.success(
        n === 1 ? '1 MAPA excluído.' : `${n} MAPAs excluídos.`,
      );
      await carregar();
    } catch (err) {
      if (!aliveRef.current) return;
      toast.error(
        err instanceof ApiRequestError
          ? err.message
          : 'Falha de comunicação com a API.',
      );
    } finally {
      if (aliveRef.current) setBusy(false);
    }
  };

  return (
    <AppShell className="flex h-dvh max-h-dvh flex-col overflow-hidden bg-surface text-text">
      <OpsPageHeader
        title="Mapas"
        rightSlot={
          <div className="flex items-center gap-0.5">
            {mapas.length > 0 ? (
              <Button
                type="button"
                variant="ghost"
                aria-label="Excluir todos os MAPAs"
                disabled={busy || loading}
                onClick={() => setConfirmDeleteAll(true)}
                className="h-11 min-h-[44px] gap-1 rounded-full border-0 bg-transparent px-2.5 text-[12px] font-bold uppercase tracking-wide text-primary-foreground shadow-none hover:bg-primary-foreground/10 focus-visible:ring-2 focus-visible:ring-brand-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-brand-navy"
              >
                <Trash2 className="h-5 w-5" strokeWidth={2.5} aria-hidden />
                <span>Todos</span>
              </Button>
            ) : null}
            <Button
              type="button"
              variant="ghost"
              aria-label="Novo MAPA"
              disabled={busy}
              onClick={novoMapa}
              className="h-11 min-h-[44px] gap-1 rounded-full border-0 bg-transparent px-2.5 text-[12px] font-bold uppercase tracking-wide text-primary-foreground shadow-none hover:bg-primary-foreground/10 focus-visible:ring-2 focus-visible:ring-brand-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-brand-navy"
            >
              <Plus className="h-5 w-5" strokeWidth={2.75} aria-hidden />
              <span>Novo</span>
            </Button>
          </div>
        }
      />

      <div className="flex min-h-0 flex-1 flex-col pb-tabbar">
        {loading ? (
          <LoadingState label="Carregando mapas…" />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void carregar()} />
        ) : mapas.length === 0 ? (
          <EmptyState
            icon={MapPinned}
            title="Nenhum MAPA cadastrado"
            description="Crie o primeiro MAPA do turno."
            action={
              <Button type="button" variant="primary" onClick={novoMapa} className="min-h-btn gap-2">
                <Plus className="h-5 w-5" aria-hidden />
                Novo MAPA
              </Button>
            }
          />
        ) : (
          <>
            <div className="shrink-0 space-y-2 border-b border-border/50 bg-surface-card px-4 py-3">
              <FilterChipsBar
                chips={chips}
                filterActive={temFiltroAtivo}
                onOpenFilters={abrirFiltro}
              />
              {temFiltroAtivo ? (
                <p className="text-xs font-medium text-text-muted">
                  {filtrados.length} resultado{filtrados.length === 1 ? '' : 's'}
                </p>
              ) : null}
            </div>

            {filtrados.length === 0 ? (
              <EmptyState
                icon={Search}
                title="Nenhum MAPA encontrado"
                description="Ajuste a busca ou os filtros e tente de novo."
                action={
                  <Button
                    type="button"
                    variant="outline"
                    onClick={limparFiltros}
                    className="min-h-btn"
                  >
                    Limpar filtros
                  </Button>
                }
              />
            ) : (
              <div className="min-h-0 flex-1 touch-pan-y overflow-y-auto overscroll-y-contain [-webkit-overflow-scrolling:touch]">
                <ul className="flex flex-col gap-2.5 p-4" role="list">
                  {filtrados.map((row) => {
                    const data = dataExibicao(row);
                    const st = statusMapaLista(row);
                    const codigo = formatCodigoMapa(row.codigo_mapa);
                    return (
                      <li key={row.id_registro}>
                        <OpsCard
                          onClick={() => abrirMapa(row.id_registro)}
                          aria-label={`Abrir MAPA ${codigo}`}
                          disabled={busy}
                          className="rounded-xl border-border/60 bg-surface-card"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-base font-bold tabular-nums text-brand-navy">
                              {codigo}
                            </p>
                            <Pill label={st.label} tone={st.tone} />
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <EmpresaChip empresa={row.empresa} />
                          </div>
                          <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-text-muted">
                            <div>
                              <dt className="font-semibold uppercase tracking-wide text-text-muted/80">
                                Turno
                              </dt>
                              <dd className="truncate font-semibold text-text">
                                {row.turno || '—'}
                              </dd>
                            </div>
                            <div>
                              <dt className="font-semibold uppercase tracking-wide text-text-muted/80">
                                Data
                              </dt>
                              <dd className="font-semibold tabular-nums text-text">
                                {data ?? '—'}
                              </dd>
                            </div>
                          </dl>
                          <p className="text-xs font-medium text-text-muted">
                            {qtdViagensLabel(row)}
                          </p>
                        </OpsCard>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </>
        )}
      </div>

      <FilterBottomSheet
        open={filtroOpen}
        onOpenChange={setFiltroOpen}
        title="Filtrar mapas"
        onClear={() => {
          limparFiltros();
          setFiltroOpen(false);
        }}
        onApply={aplicarFiltro}
      >
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
            aria-hidden
          />
          <Input
            type="search"
            value={draftBusca}
            onChange={(e) => setDraftBusca(e.target.value)}
            placeholder="Buscar nº, empresa, linha ou turno"
            aria-label="Buscar"
            className="h-11 pl-9"
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="mapa-filtro-turno">Turno</Label>
          <Select
            value={draftTurno || FILTRO_TODOS}
            onValueChange={(v) => setDraftTurno(v === FILTRO_TODOS ? '' : v)}
          >
            <SelectTrigger id="mapa-filtro-turno" className="h-11">
              <SelectValue placeholder="Todos" />
            </SelectTrigger>
            <SelectContent position="popper" className="z-[300]">
              <SelectItem value={FILTRO_TODOS}>Todos</SelectItem>
              {turnosOpcoes.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="mapa-filtro-linha">Linha</Label>
          <Select
            value={draftLinha || FILTRO_TODOS}
            onValueChange={(v) => setDraftLinha(v === FILTRO_TODOS ? '' : v)}
          >
            <SelectTrigger id="mapa-filtro-linha" className="h-11">
              <SelectValue placeholder="Todas" />
            </SelectTrigger>
            <SelectContent position="popper" className="z-[300]">
              <SelectItem value={FILTRO_TODOS}>Todas</SelectItem>
              {linhasOpcoes.map((l) => (
                <SelectItem key={l} value={l}>
                  {l}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </FilterBottomSheet>

      <ConfirmDialog
        open={confirmDeleteAll}
        title="Excluir todos"
        message={`Exclui os ${mapas.length} MAPA${mapas.length === 1 ? '' : 's'} cadastrados, com carros e viagens. Esta ação não pode ser desfeita. Continuar?`}
        confirmLabel="Excluir todos"
        onConfirm={() => void confirmarExcluirTodos()}
        onCancel={() => setConfirmDeleteAll(false)}
      />
    </AppShell>
  );
}
