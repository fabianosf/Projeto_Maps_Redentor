import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { listMapas } from '@/api/mapa';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaListaItem } from '@/types/mapa';
import { apiErrorMessage } from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

/** Tela 04 — Lista MAPA (RF-MAP-UI-001..004) */
export function ListaMapaScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  useScreenBg(MAPA_BG);

  const [mapas, setMapas] = useState<MapaListaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { response, data } = await listMapas();
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        setError(apiErrorMessage(data, 'Falha ao carregar mapas.'));
        setMapas([]);
        return;
      }
      setMapas(data.mapas);
    } catch {
      setError('Não foi possível conectar à API.');
      setMapas([]);
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
    <div className="page h-dvh max-h-dvh overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader
        title="CADASTRO DE MAPAS"
        onBack={() => navigate('/principal')}
        rightSlot={
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Incluir mapa"
            onClick={() => navigate('/mapas')}
            className="h-9 w-9 rounded-full bg-white text-primary hover:bg-white/90"
          >
            <Plus className="h-5 w-5" strokeWidth={2.75} />
          </Button>
        }
      />

      <div className="flex min-h-0 flex-1 flex-col bg-[#B9C8D4]">
        <div className="min-h-0 flex-1 touch-pan-y overflow-y-auto overscroll-y-contain [-webkit-overflow-scrolling:touch]">
          {loading ? (
            <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>
          ) : error ? (
            <div className="flex flex-col items-center gap-3 p-6">
              <p className="text-center text-sm font-medium text-red-800">{error}</p>
              <Button type="button" className="min-w-[140px]" onClick={() => void carregar()}>
                Tentar novamente
              </Button>
            </div>
          ) : mapas.length === 0 ? (
            <p className="p-6 text-center text-sm font-medium text-slate-700">
              Nenhum MAPA cadastrado. Toque em + para criar.
            </p>
          ) : (
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
                        {Number.isFinite(Number(row.cod_map))
                          ? Math.trunc(Number(row.cod_map))
                          : i + 1}
                      </td>
                      <td className="max-w-[140px] truncate px-2 py-3.5 text-center font-semibold">
                        {row.linha}
                      </td>
                      <td className="px-2 py-3.5 text-center font-semibold">{row.turno}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
