import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { ApiRequestError } from '@/api/client';
import { listMapas } from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaListaItem } from '@/types/mapa';
import { formatCodMap } from '@/utils/mapaFormat';

const BG = '#B9C8D4';

/** Tela 04 — Lista MAPA */
export function MapasListScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  useScreenBg(BG);

  const [mapas, setMapas] = useState<MapaListaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listMapas();
      setMapas(data.mapas);
    } catch (e) {
      setMapas([]);
      setError(
        e instanceof ApiRequestError
          ? e.message
          : 'Não foi possível conectar à API.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar, location.key]);

  useEffect(() => {
    const onFocus = () => {
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

  return (
    <AppShell className="flex h-dvh max-h-dvh flex-col overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader
        title="CADASTRO DE MAPAS"
        onBack={() => navigate('/principal')}
        rightSlot={
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Incluir mapa"
            onClick={() => navigate('/mapas/novo')}
            className="h-9 w-9 rounded-full bg-white text-primary hover:bg-white/90"
          >
            <Plus className="h-5 w-5" strokeWidth={2.75} />
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
            description="Toque em + para criar."
            action={
              <Button type="button" onClick={() => navigate('/mapas/novo')}>
                Novo MAPA
              </Button>
            }
          />
        ) : (
          <div className="min-h-0 flex-1 touch-pan-y overflow-y-auto overscroll-y-contain [-webkit-overflow-scrolling:touch]">
            <div className="border-y border-slate-400/40 bg-white/70">
              <table className="w-full caption-bottom border-collapse text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="border-b-2 border-slate-500/40 bg-[#A8B9C9]">
                    <th className="px-2 py-3.5 text-center text-[13px] font-bold uppercase tracking-wide text-slate-900">
                      Número
                    </th>
                    <th className="px-2 py-3.5 text-center text-[13px] font-bold uppercase tracking-wide text-slate-900">
                      Linha
                    </th>
                    <th className="px-2 py-3.5 text-center text-[13px] font-bold uppercase tracking-wide text-slate-900">
                      Turno
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {mapas.map((row, i) => (
                    <tr
                      key={row.id_registro}
                      className={`cursor-pointer border-b border-border/50 text-slate-900 ${
                        i % 2 === 0 ? 'bg-white' : 'bg-[#E8EEF4]'
                      }`}
                      onClick={() => navigate(`/mapas/${row.id_registro}`)}
                    >
                      <td className="px-2 py-3.5 text-center font-semibold">
                        {formatCodMap(row.cod_map)}
                      </td>
                      <td className="max-w-[140px] truncate px-2 py-3.5 text-center font-semibold">
                        {row.linha ?? '—'}
                      </td>
                      <td className="px-2 py-3.5 text-center font-semibold">{row.turno}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
