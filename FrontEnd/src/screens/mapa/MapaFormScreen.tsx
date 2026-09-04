import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ClipboardList } from 'lucide-react';
import { toast } from 'sonner';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import { createMapa, getMapa, updateMapa } from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { DatePickerField } from '@/components/forms/DatePickerField';
import { Button } from '@/components/ui/button';
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
import type { CadastrosMestres } from '@/types/cadastro';
import type { MapaHeaderPayload } from '@/types/mapa';
import {
  brToYmd,
  combineDateAndTime,
  formatHora,
  isValidHHMM,
  parseDateBR,
  toDateBR,
  todayBR,
} from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

/** Opções fixas do combo Empresa (sempre renderizadas). */
const EMPRESA_OPCOES = ['Futuro', 'Redentor', 'Barra'] as const;

/** Opções fixas do combo Turno (sempre renderizadas). */
const TURNO_OPCOES = ['TURNO 01', 'TURNO 02', 'TURNO 03'] as const;

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

function normalizeEmpresaLabel(raw: string): string {
  const t = raw.trim().toLowerCase();
  const found = EMPRESA_OPCOES.find((o) => o.toLowerCase() === t);
  return found ?? EMPRESA_OPCOES[0];
}

function normalizeTurnoLabel(raw: string): string {
  const t = raw.trim().toUpperCase();
  const found = TURNO_OPCOES.find((o) => o === t);
  if (found) return found;
  const num = t.replace(/\D/g, '');
  if (num) {
    const byCode = TURNO_OPCOES.find((o) => o.endsWith(num.padStart(2, '0')));
    if (byCode) return byCode;
  }
  return TURNO_OPCOES[0];
}

/**
 * Cadastro / edição de cabeçalho do MAPA.
 * Rotas: `/mapas/novo` | `/mapas/:id/editar`
 */
export function MapaFormScreen() {
  const navigate = useNavigate();
  const { id: idParam } = useParams();
  const idRegistro = idParam ? Number(idParam) : null;
  const isEdit = idRegistro != null && Number.isFinite(idRegistro);
  const { user } = useAuth();
  useScreenBg(MAPA_BG);

  const matriculaRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [matricula, setMatricula] = useState('');
  const [dataBR, setDataBR] = useState('');
  const [inicioHHMM, setInicioHHMM] = useState('');
  const [fimHHMM, setFimHHMM] = useState('');
  const [empresa, setEmpresa] = useState<string>(EMPRESA_OPCOES[0]);
  const [idLinha, setIdLinha] = useState('');
  const [codigoLinha, setCodigoLinha] = useState('');
  const [turno, setTurno] = useState<string>(TURNO_OPCOES[0]);

  const todasLinhas = useMemo(() => cadastros?.linhas ?? [], [cadastros]);

  const resolveEmpresaId = (label: string): number | null => {
    const nome = normalizeEmpresaLabel(label);
    const list = cadastros?.empresas ?? [];
    const byDesc = list.find(
      (e) => String(e.descricao).trim().toLowerCase() === nome.toLowerCase(),
    );
    if (byDesc) return Number(toId(byDesc.id_empresa));
    const codigo = EMPRESA_OPCOES.indexOf(nome as (typeof EMPRESA_OPCOES)[number]) + 1;
    const byCodigo = list.find((e) => Number(e.codigo_empresa) === codigo);
    if (byCodigo) return Number(toId(byCodigo.id_empresa));
    return codigo > 0 ? codigo : null;
  };

  const resolveTurnoId = (label: string): number | null => {
    const nome = normalizeTurnoLabel(label);
    const list = cadastros?.turnos ?? [];
    const byDesc = list.find(
      (t) => String(t.descricao).trim().toUpperCase() === nome,
    );
    if (byDesc) return Number(toId(byDesc.id_turno));
    const codigo = TURNO_OPCOES.indexOf(nome as (typeof TURNO_OPCOES)[number]) + 1;
    const byCodigo = list.find((t) => Number(t.codigo_turno) === codigo);
    if (byCodigo) return Number(toId(byCodigo.id_turno));
    return codigo > 0 ? codigo : null;
  };

  const goLista = () => navigate('/mapas', { replace: true });

  useEffect(() => {
    if (user?.matricula) setMatricula(String(user.matricula));
  }, [user?.matricula]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const cadRes = await getCadastros();
        if (cancelled) return;

        const cad = cadRes.cadastros;
        setCadastros(cad);

        if (isEdit && idRegistro != null) {
          const mapRes = await getMapa(idRegistro);
          if (cancelled) return;
          const m = mapRes.mapa;
          setDataBR(toDateBR(m.data) || todayBR());
          setInicioHHMM(formatHora(m.inicio_jornada_des).replace('—', ''));
          setFimHHMM(formatHora(m.fim_jornada_des).replace('—', ''));
          setIdLinha(toId(m.id_linha));
          setEmpresa(normalizeEmpresaLabel(String(m.empresa ?? EMPRESA_OPCOES[0])));
          setTurno(normalizeTurnoLabel(String(m.turno ?? TURNO_OPCOES[0])));
          const linha = cad.linhas.find((l) => toId(l.id_linha) === toId(m.id_linha));
          if (linha) {
            setCodigoLinha(String(linha.codigo_linha ?? linha.descricao ?? ''));
            if (linha.empresa) setEmpresa(normalizeEmpresaLabel(String(linha.empresa)));
          }
        } else {
          setDataBR(todayBR());
          setEmpresa(EMPRESA_OPCOES[0]);
          setTurno(TURNO_OPCOES[0]);
        }
      } catch (e) {
        if (!cancelled) {
          const msg =
            e instanceof ApiRequestError
              ? e.message
              : 'Falha de comunicação com a API.';
          toast.error(msg);
          if (isEdit) goLista();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carga inicial
  }, [idRegistro, isEdit]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const dataOk = parseDateBR(dataBR);
    if (!dataOk) {
      toast.error('Data inválida. Use o formato dd/mm/aaaa.');
      return;
    }
    if (!isValidHHMM(inicioHHMM)) {
      toast.error('Início da jornada inválido. Use HH:MM.');
      return;
    }
    if (fimHHMM.trim() && !isValidHHMM(fimHHMM)) {
      toast.error('Fim da jornada inválido. Use HH:MM.');
      return;
    }

    const codigoLinhaTrim = codigoLinha.trim();
    if (!codigoLinhaTrim) {
      toast.error('O campo Linha é obrigatório.');
      return;
    }
    if (!Number.isFinite(Number(codigoLinhaTrim)) || Number(codigoLinhaTrim) <= 0) {
      toast.error('Informe um código de Linha válido.');
      return;
    }

    const turnoSelecionado = normalizeTurnoLabel(turno);
    if (!turno?.trim() || !TURNO_OPCOES.includes(turnoSelecionado as (typeof TURNO_OPCOES)[number])) {
      toast.error('O campo Turno é obrigatório.');
      return;
    }

    const idEmpresaNum = resolveEmpresaId(empresa);
    const idTurnoNum = resolveTurnoId(turnoSelecionado);
    // Seeds usam PK a partir de 0 — não tratar 0 como "ausente".
    if (idEmpresaNum == null || !Number.isFinite(idEmpresaNum)) {
      toast.error('Selecione a empresa.');
      return;
    }
    if (idTurnoNum == null || !Number.isFinite(idTurnoNum)) {
      toast.error('O campo Turno é obrigatório.');
      return;
    }

    let linhaId = idLinha;
    if (linhaId === '') {
      const codigoNum = Number(codigoLinhaTrim);
      const byCode = todasLinhas.find((l) => {
        const c = Number(l.codigo_linha);
        return (
          (Number.isFinite(codigoNum) && c === codigoNum) ||
          String(l.codigo_linha ?? '') === codigoLinhaTrim ||
          String(l.descricao ?? '').trim() === codigoLinhaTrim
        );
      });
      if (byCode) linhaId = toId(byCode.id_linha);
    }

    const codigoTurno =
      TURNO_OPCOES.indexOf(turnoSelecionado as (typeof TURNO_OPCOES)[number]) + 1;

    const payload: MapaHeaderPayload = {
      codigo_linha: Number(codigoLinhaTrim),
      id_empresa: Number(idEmpresaNum),
      id_turno: Number(idTurnoNum),
      codigo_turno: Number(codigoTurno),
      turno: turnoSelecionado,
      data: brToYmd(dataOk),
      inicio_jornada_des: combineDateAndTime(dataOk, inicioHHMM),
      fim_jornada_des: fimHHMM.trim()
        ? combineDateAndTime(dataOk, fimHHMM)
        : null,
      observacao: null,
    };
    if (linhaId !== '' && Number.isFinite(Number(linhaId))) {
      payload.id_linha = Number(linhaId);
    }

    setBusy(true);
    try {
      if (isEdit && idRegistro != null) {
        await updateMapa(idRegistro, payload);
        toast.success('MAPA atualizado com sucesso.');
        navigate(`/mapas/${idRegistro}`, { replace: true });
      } else {
        const res = await createMapa(payload);
        toast.success('MAPA cadastrado com sucesso.');
        navigate(`/mapas/${res.mapa.id_registro}`, { replace: true });
      }
    } catch (err) {
      const msg =
        err instanceof ApiRequestError
          ? err.message
          : 'Falha de comunicação com a API.';
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <AppShell className="bg-[#B9C8D4]">
        <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
          <PageHeader title="MAPA" onBack={goLista} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-[#B9C8D4]">
      <div className="page flex min-h-dvh flex-col bg-[#B9C8D4] text-slate-900">
        <PageHeader
          title="MAPA"
          onBack={goLista}
          rightSlot={
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Abrir detalhe do MAPA"
              onClick={() => {
                if (!isEdit || idRegistro == null) {
                  toast.message('Salve o MAPA antes de abrir os registros.');
                  return;
                }
                navigate(`/mapas/${idRegistro}`);
              }}
              className="h-9 w-9 rounded border border-white/70 text-white hover:bg-white/10"
            >
              <ClipboardList className="h-5 w-5" strokeWidth={2.25} />
            </Button>
          }
        />

        <form
          className="page-body flex min-h-0 flex-1 flex-col bg-[#B9C8D4]"
          onSubmit={(e) => void onSubmit(e)}
          autoComplete="off"
        >
          <div className="field-stack">
            <div className="grid grid-cols-2 items-start gap-3">
              <FormField
                ref={matriculaRef}
                label="MATRÍCULA"
                name="matricula"
                value={matricula}
                readOnly
                disabled
                className="bg-white"
              />
              <DatePickerField label="DATA" value={dataBR} onChange={setDataBR} />
            </div>

            <div className="flex w-full flex-col gap-1.5">
              <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                Empresa
              </Label>
              <Select value={empresa} onValueChange={setEmpresa}>
                <SelectTrigger className="h-12 w-full rounded-lg border-slate-400 bg-white text-base text-slate-900">
                  <SelectValue placeholder="Futuro" />
                </SelectTrigger>
                <SelectContent position="popper" className="z-[300]">
                  {EMPRESA_OPCOES.map((nome) => (
                    <SelectItem key={nome} value={nome}>
                      {nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

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
                label="FIM DE JORNADA"
                name="fim"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                maxLength={5}
                value={fimHHMM}
                onChange={(e) => setFimHHMM(maskHHMM(e.target.value))}
                className="bg-white"
              />
            </div>

            <div className="grid grid-cols-2 items-start gap-3">
              <FormField
                label="LINHA"
                name="linha"
                requiredMark
                required
                inputMode="numeric"
                placeholder="000"
                value={codigoLinha}
                onChange={(e) => {
                  const v = e.target.value;
                  setCodigoLinha(v);
                  const codigoNum = Number(v.trim());
                  const linha = todasLinhas.find((l) => {
                    const c = Number(l.codigo_linha);
                    return (
                      (Number.isFinite(codigoNum) && c === codigoNum) ||
                      String(l.codigo_linha ?? '') === v.trim() ||
                      String(l.descricao ?? '').trim() === v.trim()
                    );
                  });
                  if (linha) {
                    setIdLinha(toId(linha.id_linha));
                    if (linha.empresa) {
                      setEmpresa(normalizeEmpresaLabel(String(linha.empresa)));
                    }
                  } else {
                    setIdLinha('');
                  }
                }}
                className="bg-white"
              />

              <div className="flex w-full flex-col gap-1.5">
                <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                  Turno <span className="req">*</span>
                </Label>
                <Select value={turno || TURNO_OPCOES[0]} onValueChange={setTurno}>
                  <SelectTrigger className="h-12 w-full rounded-lg border-slate-400 bg-white text-base text-slate-900">
                    <SelectValue placeholder="TURNO 01" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="z-[300]">
                    {TURNO_OPCOES.map((nome) => (
                      <SelectItem key={nome} value={nome}>
                        {nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
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
    </AppShell>
  );
}
