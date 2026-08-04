import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Plus, Route } from 'lucide-react';
import { toast } from 'sonner';
import { getMapa } from '@/api/mapa';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaCompleto, MapaItem } from '@/types/mapa';
import { apiErrorMessage, formatHora } from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

function formatCarro(item: MapaItem): string {
  const frota = item.numero_frota ?? String(item.id_veiculo ?? '');
  const digits = String(frota).replace(/\D/g, '');
  if (digits && Number.isFinite(Number(digits))) {
    return String(Math.trunc(Number(digits))).padStart(5, '0');
  }
  return String(frota || '—');
}

/** Tela 06 — Registros (itens de tb_item_map do MAPA). */
export function RegistrosMapaScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const { idRegistro: idParam } = useParams();
  const idRegistro = Number(idParam);
  useScreenBg(MAPA_BG);

  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const goCadastroMapa = useCallback(() => {
    if (Number.isFinite(idRegistro)) {
      navigate(`/mapas/${idRegistro}`);
      return;
    }
    navigate('/mapas');
  }, [idRegistro, navigate]);

  const carregar = useCallback(async () => {
    if (!Number.isFinite(idRegistro)) {
      navigate('/lista-mapa', { replace: true });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { response, data } = await getMapa(idRegistro);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        setError(apiErrorMessage(data, 'Falha ao carregar registros.'));
        setMapa(null);
        return;
      }
      setMapa(data.mapa);
    } catch {
      setError('Não foi possível conectar à API.');
      setMapa(null);
    } finally {
      setLoading(false);
    }
  }, [idRegistro, navigate]);

  useEffect(() => {
    void carregar();
  }, [carregar, location.key]);

  const itens = mapa?.itens ?? [];

  const abrirViagem = () => {
    if (selectedId == null) {
      toast.message('Selecione um registro para abrir as viagens.');
      return;
    }
    navigate(`/mapas/${idRegistro}/registros/${selectedId}/viagens`);
  };

  return (
    <div className="page h-dvh max-h-dvh overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader
        title="REGISTROS"
        onBack={goCadastroMapa}
        rightSlot={
          <Button
            type="button"
            variant="ghost"
            aria-label="Viagem"
            onClick={abrirViagem}
            className="h-9 gap-1 rounded-md border border-white/70 px-2 text-white hover:bg-white/10"
          >
            <Route className="h-4 w-4" strokeWidth={2.25} />
            <span className="text-[11px] font-bold uppercase tracking-wide">Viagem</span>
          </Button>
        }
      />

      <div className="flex min-h-0 flex-1 flex-col bg-[#B9C8D4]">
        <div className="flex shrink-0 justify-end px-4 py-3">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Incluir registro"
            onClick={() => navigate(`/mapas/${idRegistro}/registros/novo`)}
            className="h-9 w-9 rounded-full bg-white text-primary hover:bg-white/90"
          >
            <Plus className="h-5 w-5" strokeWidth={2.75} />
          </Button>
        </div>

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
          ) : (
            <div className="border-y border-slate-400/40 bg-white/70">
              <table className="w-full caption-bottom border-collapse text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="border-b-2 border-slate-500/40 bg-[#A8B9C9]">
                    <th className="px-1.5 py-3.5 text-center text-[12px] font-bold uppercase tracking-wide text-slate-900">
                      Carro
                    </th>
                    <th className="px-1.5 py-3.5 text-center text-[12px] font-bold uppercase tracking-wide text-slate-900">
                      Matrícula
                    </th>
                    <th className="px-1.5 py-3.5 text-center text-[12px] font-bold uppercase tracking-wide text-slate-900">
                      Início (Jornada)
                    </th>
                    <th className="px-1.5 py-3.5 text-center text-[12px] font-bold uppercase tracking-wide text-slate-900">
                      Chegada ao Ponto
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {itens.map((item, i) => {
                    const selected = item.id_item === selectedId;
                    return (
                      <tr
                        key={item.id_item}
                        className={`cursor-pointer border-b border-border/50 text-slate-900 ${
                          selected
                            ? 'bg-primary/15'
                            : i % 2 === 0
                              ? 'bg-white'
                              : 'bg-[#E8EEF4]'
                        }`}
                        onClick={() => {
                          if (selected) {
                            navigate(`/mapas/${idRegistro}/registros/${item.id_item}`);
                            return;
                          }
                          setSelectedId(item.id_item);
                        }}
                      >
                        <td className="px-1.5 py-3.5 text-center font-semibold">
                          {formatCarro(item)}
                        </td>
                        <td className="px-1.5 py-3.5 text-center font-semibold">
                          {item.matricula_motorista ?? '—'}
                        </td>
                        <td className="px-1.5 py-3.5 text-center font-semibold">
                          {formatHora(item.hor_ini_jor)}
                        </td>
                        <td className="px-1.5 py-3.5 text-center font-semibold">
                          {formatHora(item.chegada_ponto)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
