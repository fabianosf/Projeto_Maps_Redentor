import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import { ApiRequestError } from '@/api/client';
import { listMapas } from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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

/** Tela 04 — Lista MAPA (UX mobile-first; mesmos dados/rotas/API). */
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
  };

  const abrirMapa = (id: number) => {
    navigate(`/mapas/${id}`);
  };

  const novoMapa = () => navigate('/mapas/novo');

  return (
    <AppShell className="flex h-dvh max-h-dvh flex-col overflow-hidden bg-screen text-slate-900">
      <PageHeader
        title="CADASTRO DE MAPAS"
        onBack={() => navigate('/principal')}
        rightSlot={
          <Button
            type="button"
            variant="ghost"
            aria-label="Novo MAPA"
            onClick={novoMapa}
            className="h-11 min-h-touch gap-1 rounded-lg border border-white/70 bg-white px-2.5 text-[12px] font-bold uppercase tracking-wide text-primary hover:bg-white/90"
          >
            <Plus className="h-5 w-5" strokeWidth={2.75} aria-hidden />
            <span>Novo</span>
          </Button>
        }
      />

      <div className="flex min-h-0 flex-1 flex-col">
        {loading ? (
          <LoadingState label="Carregando mapas…" />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void carregar()} />
        ) : mapas.length === 0 ? (
          <EmptyState
            title="Nenhum MAPA cadastrado"
            description="Toque em + Novo para criar o primeiro MAPA."
            action={
              <Button
                type="button"
                onClick={novoMapa}
                className="min-h-touch gap-2"
              >
                <Plus className="h-5 w-5" aria-hidden />
                Novo MAPA
              </Button>
            }
          />
        ) : (
          <>
            <section
              className="toolbar-actions shrink-0 flex-col space-y-3 border-b border-border/60 bg-card/70 px-4 py-3"
              aria-label="Busca e filtros"
            >
              <div className="relative w-full">
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground"
                  aria-hidden
                />
                <Input
                  type="search"
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  placeholder="Buscar nº, linha ou turno"
                  aria-label="Buscar por número, linha ou turno"
                  className="h-11 min-h-touch border-input bg-card pl-10 text-base"
                />
              </div>

              <div className="grid w-full grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <Label
                    htmlFor="filtro-turno"
                    className="text-section uppercase text-foreground"
                  >
                    Turno
                  </Label>
                  <Select
                    value={filtroTurno || FILTRO_TODOS}
                    onValueChange={(v) =>
                      setFiltroTurno(v === FILTRO_TODOS ? '' : v)
                    }
                  >
                    <SelectTrigger
                      id="filtro-turno"
                      className="h-11 min-h-touch border-input bg-card text-base"
                    >
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
                  <Label
                    htmlFor="filtro-linha"
                    className="text-section uppercase text-foreground"
                  >
                    Linha
                  </Label>
                  <Select
                    value={filtroLinha || FILTRO_TODOS}
                    onValueChange={(v) =>
                      setFiltroLinha(v === FILTRO_TODOS ? '' : v)
                    }
                  >
                    <SelectTrigger
                      id="filtro-linha"
                      className="h-11 min-h-touch border-slate-400 bg-white text-base"
                    >
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
              </div>

              {temFiltroAtivo ? (
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-slate-700">
                    {filtrados.length} resultado
                    {filtrados.length === 1 ? '' : 's'}
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={limparFiltros}
                    className="h-11 min-h-touch px-3 text-sm"
                  >
                    Limpar filtros
                  </Button>
                </div>
              ) : null}
            </section>

            {filtrados.length === 0 ? (
              <EmptyState
                title="Nenhum MAPA encontrado"
                description="Ajuste a busca ou os filtros e tente de novo."
                action={
                  <Button
                    type="button"
                    variant="outline"
                    onClick={limparFiltros}
                    className="min-h-touch"
                  >
                    Limpar filtros
                  </Button>
                }
              />
            ) : (
              <div className="min-h-0 flex-1 touch-pan-y overflow-y-auto overscroll-y-contain [-webkit-overflow-scrolling:touch]">
                {/* Mobile: cards */}
                <ul className="flex flex-col gap-3 p-4 md:hidden" role="list">
                  {filtrados.map((row) => {
                    const data = dataExibicao(row);
                    const linha = row.linha?.trim() ? row.linha : '—';
                    return (
                      <li key={row.id_registro}>
                        <button
                          type="button"
                          onClick={() => abrirMapa(row.id_registro)}
                          className="list-card"
                        >
                          <div className="flex items-baseline justify-between gap-3">
                            <span className="text-lg font-bold tabular-nums text-primary">
                              {formatCodigoMapa(row.codigo_mapa)}
                            </span>
                            {data ? (
                              <span className="text-sm font-medium text-slate-600">
                                {data}
                              </span>
                            ) : null}
                          </div>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[15px] font-semibold text-slate-900">
                            <span className="max-w-full truncate">
                              <span className="sr-only">Linha </span>
                              {linha}
                            </span>
                            <span className="text-slate-400" aria-hidden>
                              ·
                            </span>
                            <span>
                              <span className="sr-only">Turno </span>
                              {row.turno}
                            </span>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>

                {/* Desktop: tabela */}
                <div className="hidden border-y border-slate-400/40 bg-white/70 md:block">
                  <table className="w-full caption-bottom border-collapse text-sm">
                    <thead className="sticky top-0 z-10">
                      <tr className="border-b-2 border-slate-500/40 bg-table-head">
                        <th className="px-3 py-3.5 text-left text-[13px] font-bold uppercase tracking-wide text-slate-900">
                          Número
                        </th>
                        <th className="px-3 py-3.5 text-left text-[13px] font-bold uppercase tracking-wide text-slate-900">
                          Linha
                        </th>
                        <th className="px-3 py-3.5 text-left text-[13px] font-bold uppercase tracking-wide text-slate-900">
                          Turno
                        </th>
                        <th className="px-3 py-3.5 text-left text-[13px] font-bold uppercase tracking-wide text-slate-900">
                          Data
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtrados.map((row, i) => {
                        const data = dataExibicao(row);
                        return (
                          <tr
                            key={row.id_registro}
                            tabIndex={0}
                            role="link"
                            aria-label={`Abrir MAPA ${formatCodigoMapa(row.codigo_mapa)}`}
                            className={`cursor-pointer border-b border-border/50 text-slate-900 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring ${
                              i % 2 === 0 ? 'bg-white' : 'bg-table-zebra'
                            }`}
                            onClick={() => abrirMapa(row.id_registro)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                abrirMapa(row.id_registro);
                              }
                            }}
                          >
                            <td className="px-3 py-3.5 text-left text-base font-semibold tabular-nums">
                              {formatCodigoMapa(row.codigo_mapa)}
                            </td>
                            <td className="max-w-[220px] truncate px-3 py-3.5 text-left text-base font-semibold">
                              {row.linha ?? '—'}
                            </td>
                            <td className="px-3 py-3.5 text-left text-base font-semibold">
                              {row.turno}
                            </td>
                            <td className="px-3 py-3.5 text-left text-base font-semibold text-slate-700">
                              {data ?? '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
