import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { createViagem, getMapa, updateViagem } from '@/api/mapa';
import { FormField } from '@/components/forms/FormField';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { MapaCompleto, ViagemPayload } from '@/types/mapa';
import {
  apiErrorMessage,
  combineDateAndTime,
  formatHora,
  isValidHHMM,
  toDateInput,
} from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

function maskHHMM(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

/** Tela Cadastrar_Viagem — inclusão/edição (tb_viagem). */
export function CadastroViagemScreen() {
  const navigate = useNavigate();
  const { idRegistro: idMapParam, idItem: idItemParam, idViagem: idViagemParam } =
    useParams();
  const idRegistro = Number(idMapParam);
  const idItem = Number(idItemParam);
  const idViagem =
    idViagemParam && idViagemParam !== 'novo' ? Number(idViagemParam) : null;
  const isEdit = idViagem != null && Number.isFinite(idViagem);
  useScreenBg(MAPA_BG);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [placa, setPlaca] = useState('');
  const [saidaHHMM, setSaidaHHMM] = useState('');
  const [chegadaHHMM, setChegadaHHMM] = useState('');
  const [qtdPassageiro, setQtdPassageiro] = useState('0');

  const goLista = () => {
    if (Number.isFinite(idRegistro) && Number.isFinite(idItem)) {
      navigate(`/mapas/${idRegistro}/registros/${idItem}/viagens`);
      return;
    }
    navigate('/lista-mapa');
  };

  useEffect(() => {
    if (!Number.isFinite(idRegistro) || !Number.isFinite(idItem)) {
      navigate('/lista-mapa', { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const { response, data } = await getMapa(idRegistro);
        if (cancelled) return;
        if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
          toast.error(apiErrorMessage(data, 'MAPA não encontrado.'));
          navigate('/lista-mapa', { replace: true });
          return;
        }
        const m = data.mapa;
        const item = m.itens.find((i) => i.id_item === idItem);
        if (!item) {
          toast.error('Registro não encontrado.');
          navigate(`/mapas/${idRegistro}/registros`, { replace: true });
          return;
        }
        setMapa(m);

        if (isEdit) {
          const viagem = item.viagens.find((v) => v.id_viagem === idViagem);
          if (!viagem) {
            toast.error('Viagem não encontrada.');
            navigate(`/mapas/${idRegistro}/registros/${idItem}/viagens`, {
              replace: true,
            });
            return;
          }
          setSaidaHHMM(
            formatHora(viagem.horario_saida) === '—'
              ? ''
              : formatHora(viagem.horario_saida),
          );
          setChegadaHHMM(
            formatHora(viagem.horario_chegada) === '—'
              ? ''
              : formatHora(viagem.horario_chegada),
          );
          // Placa = HH:MM próprio da viagem (não confundir com placa do veículo)
          const placaHora = String(viagem.placa ?? '').trim();
          setPlaca(
            isValidHHMM(placaHora)
              ? placaHora
              : formatHora(placaHora) === '—'
                ? ''
                : formatHora(placaHora),
          );
          const total =
            (Number(viagem.qtd_pas_ida) || 0) + (Number(viagem.qtd_pas_volta) || 0);
          setQtdPassageiro(String(total));
        } else {
          setSaidaHHMM('');
          setChegadaHHMM('');
          setPlaca('');
          setQtdPassageiro('0');
        }
      } catch {
        if (!cancelled) toast.error('Falha de comunicação com a API.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [idRegistro, idItem, idViagem, isEdit, navigate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || !mapa) return;

    if (!saidaHHMM || !isValidHHMM(saidaHHMM)) {
      toast.error('Saída da viagem inválida (HH:MM).');
      return;
    }
    if (!chegadaHHMM || !isValidHHMM(chegadaHHMM)) {
      toast.error('Chegada inválida (HH:MM).');
      return;
    }
    if (!placa || !isValidHHMM(placa)) {
      toast.error('Placa inválida (HH:MM).');
      return;
    }
    const qtd = Number(qtdPassageiro);
    if (!Number.isFinite(qtd) || qtd < 0) {
      toast.error('Qtd passageiro inválida.');
      return;
    }

    const dataMapa = toDateInput(mapa.data) || toDateInput(mapa.inicio_jornada_des);
    // Campos separados: saida / chegada / placa — sem troca de valores
    const payload: ViagemPayload = {
      horario_saida: dataMapa ? combineDateAndTime(dataMapa, saidaHHMM) : saidaHHMM,
      horario_chegada: dataMapa
        ? combineDateAndTime(dataMapa, chegadaHHMM)
        : chegadaHHMM,
      placa,
      qtd_passageiro: Math.trunc(qtd),
      qtd_pas_ida: Math.trunc(qtd),
      qtd_pas_volta: 0,
    };

    setBusy(true);
    try {
      const { response, data } =
        isEdit && idViagem != null
          ? await updateViagem(idViagem, payload)
          : await createViagem(idItem, payload);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        toast.error(apiErrorMessage(data, 'Falha ao salvar viagem.'));
        return;
      }
      toast.success(isEdit ? 'Viagem atualizada.' : 'Viagem cadastrada.');
      goLista();
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
        <PageHeader title="CADASTRAR VIAGEM" onBack={goLista} />
        <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
      <PageHeader title="CADASTRAR VIAGEM" onBack={goLista} />

      <form
        className="page-body bg-[#B9C8D4]"
        onSubmit={(e) => void onSubmit(e)}
        autoComplete="off"
      >
        <div className="field-stack">
          <div className="grid grid-cols-2 items-start gap-3">
            <FormField
              label="SAÍDA VIAGEM"
              name="saida"
              requiredMark
              type="text"
              inputMode="numeric"
              placeholder="HH:MM"
              maxLength={5}
              value={saidaHHMM}
              onChange={(e) => setSaidaHHMM(maskHHMM(e.target.value))}
              className="bg-white"
            />
            <FormField
              label="CHEGADA"
              name="chegada"
              requiredMark
              type="text"
              inputMode="numeric"
              placeholder="HH:MM"
              maxLength={5}
              value={chegadaHHMM}
              onChange={(e) => setChegadaHHMM(maskHHMM(e.target.value))}
              className="bg-white"
            />
          </div>

          <FormField
            label="PLACA"
            name="placa"
            requiredMark
            type="text"
            inputMode="numeric"
            placeholder="HH:MM"
            maxLength={5}
            value={placa}
            onChange={(e) => setPlaca(maskHHMM(e.target.value))}
            className="bg-white"
          />

          <FormField
            label="QTD PASSAGEIRO"
            name="qtd"
            requiredMark
            inputMode="numeric"
            placeholder="0"
            value={qtdPassageiro}
            onChange={(e) =>
              setQtdPassageiro(e.target.value.replace(/\D/g, '').slice(0, 5))
            }
            className="bg-white"
          />
        </div>

        <div className="mt-auto grid grid-cols-2 gap-3 border-t border-slate-400/40 pt-5">
          <Button type="submit" disabled={busy} className="h-12 text-base font-bold uppercase">
            {busy ? 'Salvando…' : 'Confirmar'}
          </Button>
          <Button
            type="button"
            disabled={busy}
            onClick={goLista}
            className="h-12 text-base font-bold uppercase"
          >
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  );
}
