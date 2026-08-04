import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { deleteViagem, getMapa } from '@/api/mapa';
import { AppAlertDialog } from '@/components/shared/AppAlertDialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaCompleto, MapaItem, MapaViagem } from '@/types/mapa';
import { apiErrorMessage, formatHora } from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

/** Tela VIAGEM — listagem de viagens do registro (tb_viagem). */
export function ViagensScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const { idRegistro: idMapParam, idItem: idItemParam } = useParams();
  const idRegistro = Number(idMapParam);
  const idItem = Number(idItemParam);
  useScreenBg(MAPA_BG);

  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  const goRegistros = useCallback(() => {
    if (Number.isFinite(idRegistro)) {
      navigate(`/mapas/${idRegistro}/registros`);
      return;
    }
    navigate('/lista-mapa');
  }, [idRegistro, navigate]);

  const carregar = useCallback(async () => {
    if (!Number.isFinite(idRegistro) || !Number.isFinite(idItem)) {
      navigate('/lista-mapa', { replace: true });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { response, data } = await getMapa(idRegistro);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        setError(apiErrorMessage(data, 'Falha ao carregar viagens.'));
        setMapa(null);
        return;
      }
      const item = data.mapa.itens.find((i) => i.id_item === idItem);
      if (!item) {
        setError('Registro não encontrado.');
        setMapa(null);
        return;
      }
      setMapa(data.mapa);
      setSelectedId((prev) => {
        if (prev != null && item.viagens.some((v) => v.id_viagem === prev)) return prev;
        return null;
      });
    } catch {
      setError('Não foi possível conectar à API.');
      setMapa(null);
    } finally {
      setLoading(false);
    }
  }, [idRegistro, idItem, navigate]);

  useEffect(() => {
    void carregar();
  }, [carregar, location.key]);

  const item: MapaItem | null = useMemo(
    () => mapa?.itens.find((i) => i.id_item === idItem) ?? null,
    [mapa, idItem],
  );
  const viagens: MapaViagem[] = item?.viagens ?? [];
  const temSelecao = selectedId != null;

  const onExcluir = async () => {
    if (selectedId == null || busy) return;
    setConfirmDelete(false);
    setBusy(true);
    try {
      const { response, data } = await deleteViagem(selectedId);
      if (!response.ok) {
        toast.error(apiErrorMessage(data, 'Falha ao excluir viagem.'));
        return;
      }
      toast.success('Viagem excluída.');
      setSelectedId(null);
      await carregar();
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page h-dvh max-h-dvh overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader title="VIAGEM" onBack={goRegistros} />

      <div className="flex min-h-0 flex-1 flex-col bg-[#B9C8D4]">
        <div className="flex shrink-0 items-center justify-end gap-2 px-4 py-3">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Incluir viagem"
            onClick={() =>
              navigate(`/mapas/${idRegistro}/registros/${idItem}/viagens/novo`)
            }
            className="h-9 w-9 rounded-full bg-white text-primary hover:bg-white/90"
          >
            <Plus className="h-5 w-5" strokeWidth={2.75} />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Editar viagem"
            disabled={!temSelecao || busy}
            onClick={() => {
              if (selectedId == null) return;
              navigate(
                `/mapas/${idRegistro}/registros/${idItem}/viagens/${selectedId}`,
              );
            }}
            className="h-9 w-9 rounded-full border border-slate-500/40 bg-white text-primary disabled:opacity-40"
          >
            <Pencil className="h-4 w-4" strokeWidth={2.25} />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Excluir viagem"
            disabled={!temSelecao || busy}
            onClick={() => setConfirmDelete(true)}
            className="h-9 w-9 rounded-full border border-slate-500/40 bg-white text-destructive disabled:opacity-40"
          >
            <Trash2 className="h-4 w-4" strokeWidth={2.25} />
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
                    <th className="px-1 py-3.5 text-center text-[11px] font-bold uppercase tracking-wide text-slate-900">
                      Saída Viagem
                    </th>
                    <th className="px-1 py-3.5 text-center text-[11px] font-bold uppercase tracking-wide text-slate-900">
                      Chegada
                    </th>
                    <th className="px-1 py-3.5 text-center text-[11px] font-bold uppercase tracking-wide text-slate-900">
                      Placa
                    </th>
                    <th className="px-1 py-3.5 text-center text-[11px] font-bold uppercase tracking-wide text-slate-900">
                      Qtd Passageiro
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {viagens.map((v, i) => {
                    const selected = v.id_viagem === selectedId;
                    const qtd =
                      (Number(v.qtd_pas_ida) || 0) + (Number(v.qtd_pas_volta) || 0);
                    const placaHora = String(v.placa ?? '').trim();
                    const placaExibicao =
                      placaHora && /^\d{2}:\d{2}/.test(placaHora)
                        ? placaHora.slice(0, 5)
                        : formatHora(placaHora);
                    return (
                      <tr
                        key={v.id_viagem}
                        className={`cursor-pointer border-b border-border/50 text-slate-900 ${
                          selected
                            ? 'bg-primary/15'
                            : i % 2 === 0
                              ? 'bg-white'
                              : 'bg-[#E8EEF4]'
                        }`}
                        onClick={() => setSelectedId(v.id_viagem)}
                      >
                        <td className="px-1 py-3.5 text-center font-semibold">
                          {formatHora(v.horario_saida)}
                        </td>
                        <td className="px-1 py-3.5 text-center font-semibold">
                          {formatHora(v.horario_chegada)}
                        </td>
                        <td className="px-1 py-3.5 text-center font-semibold">
                          {placaExibicao}
                        </td>
                        <td className="px-1 py-3.5 text-center font-semibold">{qtd}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <AppAlertDialog
        open={confirmDelete}
        title="Excluir viagem"
        message="Excluir a viagem selecionada? Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        onConfirm={() => void onExcluir()}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
