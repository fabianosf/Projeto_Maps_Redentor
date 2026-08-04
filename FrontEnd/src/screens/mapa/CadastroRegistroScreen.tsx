import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { createItem, getCadastros, getMapa, updateItem } from '@/api/mapa';
import { FormField } from '@/components/forms/FormField';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { CadastrosMestres, ItemMapPayload, MapaCompleto } from '@/types/mapa';
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

function toId(v: unknown): string {
  if (v == null || v === '') return '';
  const n = Number(v);
  return Number.isFinite(n) ? String(Math.trunc(n)) : String(v).trim();
}

function formatFrotaDisplay(frota: string | number | null | undefined): string {
  const digits = String(frota ?? '').replace(/\D/g, '');
  if (digits && Number.isFinite(Number(digits))) {
    return String(Math.trunc(Number(digits))).padStart(5, '0');
  }
  return String(frota ?? '');
}

/** Tela 07 — Cadastro de Registro (tb_item_map). */
export function CadastroRegistroScreen() {
  const navigate = useNavigate();
  const { idRegistro: idMapParam, idItem: idItemParam } = useParams();
  const idRegistro = Number(idMapParam);
  const idItem = idItemParam && idItemParam !== 'novo' ? Number(idItemParam) : null;
  const isEdit = idItem != null && Number.isFinite(idItem);
  useScreenBg(MAPA_BG);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [carro, setCarro] = useState('');
  const [matricula, setMatricula] = useState('');
  const [inicioHHMM, setInicioHHMM] = useState('');
  const [chegadaHHMM, setChegadaHHMM] = useState('');

  const goRegistros = () => {
    if (Number.isFinite(idRegistro)) {
      navigate(`/mapas/${idRegistro}/registros`);
      return;
    }
    navigate('/lista-mapa');
  };

  const veiculos = useMemo(() => cadastros?.veiculos ?? [], [cadastros]);
  const motoristas = useMemo(() => cadastros?.motoristas ?? [], [cadastros]);

  useEffect(() => {
    if (!Number.isFinite(idRegistro)) {
      navigate('/lista-mapa', { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [mapRes, cadRes] = await Promise.all([getMapa(idRegistro), getCadastros()]);
        if (cancelled) return;

        if (!mapRes.response.ok || !mapRes.data || !('ok' in mapRes.data) || mapRes.data.ok !== true) {
          toast.error(apiErrorMessage(mapRes.data, 'MAPA não encontrado.'));
          navigate('/lista-mapa', { replace: true });
          return;
        }

        const m = mapRes.data.mapa;
        setMapa(m);

        let cads: CadastrosMestres | null = null;
        if (cadRes.response.ok && cadRes.data && 'ok' in cadRes.data && cadRes.data.ok === true) {
          cads = cadRes.data.cadastros;
          setCadastros(cads);
        }

        if (isEdit) {
          const item = m.itens.find((i) => i.id_item === idItem);
          if (!item) {
            toast.error('Registro não encontrado.');
            navigate(`/mapas/${idRegistro}/registros`, { replace: true });
            return;
          }
          const veiculo = cads?.veiculos.find((v) => toId(v.id_veiculo) === toId(item.id_veiculo));
          setCarro(
            formatFrotaDisplay(item.numero_frota ?? veiculo?.numero_frota ?? item.id_veiculo),
          );
          setMatricula(String(item.matricula_motorista ?? ''));
          setInicioHHMM(formatHora(item.hor_ini_jor) === '—' ? '' : formatHora(item.hor_ini_jor));
          setChegadaHHMM(
            formatHora(item.chegada_ponto) === '—' ? '' : formatHora(item.chegada_ponto),
          );
        } else {
          setCarro('');
          setMatricula('');
          setInicioHHMM(
            formatHora(m.inicio_jornada_des) === '—' ? '' : formatHora(m.inicio_jornada_des),
          );
          setChegadaHHMM('');
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
  }, [idRegistro, idItem, isEdit, navigate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || !mapa) return;

    const carroTrim = carro.trim();
    const matTrim = matricula.trim();
    if (!carroTrim || !matTrim) {
      toast.error('Carro e matrícula são obrigatórios.');
      return;
    }

    const frotaDigits = carroTrim.replace(/\D/g, '');
    const matDigits = matTrim.replace(/\D/g, '');

    if (inicioHHMM && !isValidHHMM(inicioHHMM)) {
      toast.error('Início de jornada inválido (HH:MM).');
      return;
    }
    if (chegadaHHMM && !isValidHHMM(chegadaHHMM)) {
      toast.error('Chegada no ponto inválida (HH:MM).');
      return;
    }

    // Data do cabeçalho do MAPA (com fallbacks — API às vezes serializa Timestamp)
    const dataMapa =
      toDateInput(mapa.data) ||
      toDateInput(mapa.inicio_jornada_des) ||
      toDateInput(mapa.fim_jornada_des);

    const toHorarioPayload = (hhmm: string): string | null => {
      if (!hhmm) return null;
      // Se a data do MAPA estiver ok, monta datetime completo; senão envia só HH:MM
      // e o backend completa com a data de tb_map.
      return dataMapa ? combineDateAndTime(dataMapa, hhmm) : hhmm;
    };

    const payload: ItemMapPayload = {
      // Backend resolve via tb_veiculo.numero_frota e tb_motorista.matricula
      numero_frota: frotaDigits || carroTrim,
      matricula: matDigits || matTrim,
      hor_ini_jor: toHorarioPayload(inicioHHMM),
      // Não enviar string vazia — MariaDB rejeita '' em DATETIME
      hor_fim_jor: null,
      chegada_ponto: toHorarioPayload(chegadaHHMM),
    };

    setBusy(true);
    try {
      // Atualiza mestres e valida localmente pela coluna matricula (evita lista stale).
      const cadRes = await getCadastros();
      let listaMot = motoristas;
      let listaVeic = veiculos;
      if (cadRes.response.ok && cadRes.data && 'ok' in cadRes.data && cadRes.data.ok === true) {
        setCadastros(cadRes.data.cadastros);
        listaMot = cadRes.data.cadastros.motoristas ?? [];
        listaVeic = cadRes.data.cadastros.veiculos ?? [];
      }

      const veiculoLocal = listaVeic.find((v) => {
        const nf = String(v.numero_frota ?? '').trim();
        const nfDigits = nf.replace(/\D/g, '');
        return nf === carroTrim || (frotaDigits !== '' && nfDigits === frotaDigits);
      });
      if (listaVeic.length > 0 && !veiculoLocal) {
        toast.error('Carro não encontrado.');
        return;
      }

      const motoristaLocal = listaMot.find((m) => {
        const mat = String(m.matricula ?? '').trim();
        const mDigits = mat.replace(/\D/g, '');
        return mat === matTrim || (matDigits !== '' && mDigits === matDigits);
      });
      if (listaMot.length > 0 && !motoristaLocal) {
        toast.error('Matrícula não encontrada.');
        return;
      }

      const { response, data } =
        isEdit && idItem != null
          ? await updateItem(idItem, payload)
          : await createItem(idRegistro, payload);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        toast.error(apiErrorMessage(data, 'Falha ao salvar registro.'));
        return;
      }
      toast.success(isEdit ? 'Registro atualizado.' : 'Registro cadastrado.');
      goRegistros();
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
        <PageHeader title="CADASTRO DE REGISTRO" onBack={goRegistros} />
        <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
      <PageHeader title="CADASTRO DE REGISTRO" onBack={goRegistros} />

      <form
        className="page-body bg-[#B9C8D4]"
        onSubmit={(e) => void onSubmit(e)}
        autoComplete="off"
      >
        <div className="field-stack">
          <FormField
            label="CARRO"
            name="carro"
            requiredMark
            required
            inputMode="numeric"
            placeholder="00000"
            value={carro}
            onChange={(e) => setCarro(e.target.value.replace(/\D/g, '').slice(0, 5))}
            className="bg-white"
          />

          <FormField
            label="MATRÍCULA"
            name="matricula"
            requiredMark
            required
            inputMode="numeric"
            placeholder="00000"
            maxLength={5}
            value={matricula}
            onChange={(e) => setMatricula(e.target.value.replace(/\D/g, '').slice(0, 5))}
            className="bg-white"
          />

          <div className="grid grid-cols-2 items-start gap-3">
            <FormField
              label="INÍCIO DE JORNADA"
              name="inicio"
              type="text"
              inputMode="numeric"
              placeholder="HH:MM"
              maxLength={5}
              value={inicioHHMM}
              onChange={(e) => setInicioHHMM(maskHHMM(e.target.value))}
              className="bg-white"
            />
            <FormField
              label="CHEGADA NO PONTO"
              name="chegada"
              type="text"
              inputMode="numeric"
              placeholder="HH:MM"
              maxLength={5}
              value={chegadaHHMM}
              onChange={(e) => setChegadaHHMM(maskHHMM(e.target.value))}
              className="bg-white"
            />
          </div>
        </div>

        <div className="mt-auto grid grid-cols-2 gap-3 border-t border-slate-400/40 pt-5">
          <Button type="submit" disabled={busy} className="h-12 text-base font-bold uppercase">
            {busy ? 'Salvando…' : 'Confirmar'}
          </Button>
          <Button
            type="button"
            disabled={busy}
            onClick={goRegistros}
            className="h-12 text-base font-bold uppercase"
          >
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  );
}
