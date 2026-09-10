import {
  useEffect,
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
  formatCodigoMapa,
  formatHora,
  isValidHHMM,
  parseDateBR,
  toDateBR,
  todayBR,
} from '@/utils/mapaFormat';
import { cancelIdleCallbackSafe, clearTimerSafe } from '@/utils/safeTiming';
import { SCREEN_BG } from '@/theme/tokens';

const MAPA_BG = SCREEN_BG;

/** Opções fixas do combo Turno (sempre renderizadas). */
const TURNO_OPCOES = ['TURNO 01', 'TURNO 02', 'TURNO 03'] as const;
const SELECT_EMPTY_EMP = '__empty_empresa__';

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
 * Criação: empresa obrigatória (gera codigo_mapa). Código não é editável.
 */
export function MapaFormScreen() {
  const navigate = useNavigate();
  const { id: idParam } = useParams();
  const idRegistro = idParam ? Number(idParam) : null;
  const isEdit = idRegistro != null && Number.isFinite(idRegistro);
  const { user } = useAuth();
  useScreenBg(MAPA_BG);

  const mountedRef = useRef(true);
  const loadAliveRef = useRef(true);
  const idleIdsRef = useRef<number[]>([]);
  const timerIdsRef = useRef<number[]>([]);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [matricula, setMatricula] = useState('');
  const [dataBR, setDataBR] = useState('');
  const [inicioHHMM, setInicioHHMM] = useState('');
  const [fimHHMM, setFimHHMM] = useState('');
  const [turno, setTurno] = useState<string>(TURNO_OPCOES[0]);
  const [idEmpresa, setIdEmpresa] = useState('');
  const [codigoMapa, setCodigoMapa] = useState('');
  const [empresaLabel, setEmpresaLabel] = useState('');

  const stillMounted = () => mountedRef.current && loadAliveRef.current;

  const limparAgendamentos = () => {
    for (const id of idleIdsRef.current) {
      cancelIdleCallbackSafe(id);
    }
    idleIdsRef.current = [];
    for (const id of timerIdsRef.current) {
      clearTimerSafe(id);
    }
    timerIdsRef.current = [];
  };

  useEffect(() => {
    mountedRef.current = true;
    loadAliveRef.current = true;
    return () => {
      mountedRef.current = false;
      loadAliveRef.current = false;
      limparAgendamentos();
      try {
        toast.dismiss();
      } catch {
        /* ignore */
      }
    };
  }, []);

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

  /** Cancelar: limpa pendências e volta à lista sem salvar/criar. */
  const onCancelar = () => {
    if (busy) return;
    loadAliveRef.current = false;
    limparAgendamentos();
    try {
      toast.dismiss();
    } catch {
      /* ignore */
    }
    navigate('/mapas', { replace: true });
  };

  useEffect(() => {
    if (user?.matricula && mountedRef.current) {
      setMatricula(String(user.matricula));
    }
  }, [user?.matricula]);

  useEffect(() => {
    loadAliveRef.current = true;
    let cancelled = false;
    (async () => {
      if (mountedRef.current) setLoading(true);
      try {
        const cadRes = await getCadastros();
        if (cancelled || !stillMounted()) return;
        setCadastros(cadRes.cadastros);

        if (isEdit && idRegistro != null) {
          const mapRes = await getMapa(idRegistro);
          if (cancelled || !stillMounted()) return;
          const m = mapRes.mapa;
          setDataBR(toDateBR(m.data) || todayBR());
          setInicioHHMM(formatHora(m.inicio_jornada_des).replace('—', ''));
          setFimHHMM(formatHora(m.fim_jornada_des).replace('—', ''));
          setTurno(normalizeTurnoLabel(String(m.turno ?? TURNO_OPCOES[0])));
          setCodigoMapa(formatCodigoMapa(m.codigo_mapa));
          setIdEmpresa(m.id_empresa != null ? toId(m.id_empresa) : '');
          setEmpresaLabel(String(m.empresa ?? '').trim());
        } else if (stillMounted()) {
          setDataBR(todayBR());
          setTurno(TURNO_OPCOES[0]);
          setCodigoMapa('');
          setIdEmpresa('');
          setEmpresaLabel('');
        }
      } catch (e) {
        if (!cancelled && stillMounted()) {
          const msg =
            e instanceof ApiRequestError
              ? e.message
              : 'Falha de comunicação com a API.';
          toast.error(msg);
          if (isEdit) navigate('/mapas', { replace: true });
        }
      } finally {
        if (!cancelled && stillMounted()) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      loadAliveRef.current = false;
      limparAgendamentos();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carga inicial
  }, [idRegistro, isEdit]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!mountedRef.current || busy) return;

    const dataOk = parseDateBR(dataBR);
    if (!dataOk) {
      toast.error('Data inválida. Use o formato dd/mm/aaaa.');
      return;
    }
    if (!isValidHHMM(inicioHHMM)) {
      toast.error('Início do plantão inválido. Use HH:MM.');
      return;
    }
    if (fimHHMM.trim() && !isValidHHMM(fimHHMM)) {
      toast.error('Fim do plantão inválido. Use HH:MM.');
      return;
    }

    const turnoSelecionado = normalizeTurnoLabel(turno);
    if (!turno?.trim() || !TURNO_OPCOES.includes(turnoSelecionado as (typeof TURNO_OPCOES)[number])) {
      toast.error('O campo Turno é obrigatório.');
      return;
    }

    const idTurnoNum = resolveTurnoId(turnoSelecionado);
    if (idTurnoNum == null || !Number.isFinite(idTurnoNum)) {
      toast.error('O campo Turno é obrigatório.');
      return;
    }

    if (!isEdit) {
      if (!idEmpresa.trim()) {
        toast.error('Selecione a empresa do MAPA.');
        return;
      }
    } else if (
      (!codigoMapa || codigoMapa === '—') &&
      !idEmpresa.trim() &&
      !empresaLabel.trim()
    ) {
      toast.error('Selecione a empresa para gerar o código do MAPA.');
      return;
    }

    const codigoTurno =
      TURNO_OPCOES.indexOf(turnoSelecionado as (typeof TURNO_OPCOES)[number]) + 1;

    const payload: MapaHeaderPayload = {
      id_turno: Number(idTurnoNum),
      codigo_turno: Number(codigoTurno),
      turno: turnoSelecionado,
      data: brToYmd(dataOk),
      inicio_jornada_des: combineDateAndTime(dataOk, inicioHHMM),
      fim_jornada_des: fimHHMM.trim()
        ? combineDateAndTime(dataOk, fimHHMM)
        : null,
      observacao: null,
      ...(!isEdit || (!codigoMapa || codigoMapa === '—')
        ? idEmpresa.trim()
          ? { id_empresa: Number(idEmpresa) }
          : {}
        : {}),
    };

    setBusy(true);
    try {
      if (isEdit && idRegistro != null) {
        await updateMapa(idRegistro, payload);
        if (!mountedRef.current) return;
        toast.success('MAPA atualizado com sucesso.');
        navigate(`/mapas/${idRegistro}`, { replace: true });
      } else {
        const res = await createMapa(payload);
        if (!mountedRef.current) return;
        const novoId = Number(res?.mapa?.id_registro);
        if (!Number.isFinite(novoId) || novoId <= 0) {
          toast.error(
            'MAPA criado, mas a API não retornou o identificador. Atualize a lista.',
          );
          navigate('/mapas', { replace: true });
          return;
        }
        const codigoGerado = formatCodigoMapa(res?.mapa?.codigo_mapa);
        toast.success(`MAPA ${codigoGerado} cadastrado com sucesso.`);
        navigate(`/mapas/${novoId}`, { replace: true });
      }
    } catch (err) {
      if (!mountedRef.current) return;
      const msg =
        err instanceof ApiRequestError
          ? err.message
          : 'Falha de comunicação com a API.';
      toast.error(msg);
    } finally {
      if (mountedRef.current) setBusy(false);
    }
  };

  if (loading) {
    return (
      <AppShell className="bg-screen">
        <div className="page min-h-dvh bg-screen text-slate-900">
          <PageHeader title="MAPA" onBack={onCancelar} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader
          title="MAPA"
          onBack={onCancelar}
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
          className="page-body flex min-h-0 flex-1 flex-col bg-screen"
          onSubmit={(e) => void onSubmit(e)}
          autoComplete="off"
        >
          <div className="field-stack">
            <div className="grid grid-cols-2 items-start gap-3">
              <FormField
                label="MATRÍCULA"
                name="matricula"
                value={matricula ?? ''}
                readOnly
                disabled
                className="bg-white"
              />
              <DatePickerField
                label="DATA"
                value={dataBR ?? ''}
                onChange={setDataBR}
              />
            </div>

            {isEdit && codigoMapa && codigoMapa !== '—' ? (
              <div className="grid grid-cols-2 items-start gap-3">
                <FormField
                  label="CÓDIGO"
                  name="codigo_mapa"
                  value={codigoMapa}
                  readOnly
                  disabled
                  className="bg-slate-100"
                />
                <FormField
                  label="EMPRESA"
                  name="empresa"
                  value={empresaLabel || idEmpresa}
                  readOnly
                  disabled
                  className="bg-slate-100"
                />
              </div>
            ) : (
              <div className="flex w-full flex-col gap-1.5">
                <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                  Empresa <span className="req">*</span>
                </Label>
                <Select
                  value={idEmpresa || SELECT_EMPTY_EMP}
                  onValueChange={(v) =>
                    setIdEmpresa(v === SELECT_EMPTY_EMP ? '' : (v ?? ''))
                  }
                >
                  <SelectTrigger className="h-12 w-full rounded-lg border-slate-400 bg-white text-base text-slate-900">
                    <SelectValue placeholder="Selecione a empresa" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="z-[300]">
                    {(cadastros?.empresas ?? []).map((emp) => (
                      <SelectItem
                        key={String(emp.id_empresa)}
                        value={toId(emp.id_empresa)}
                      >
                        {emp.descricao}
                        {emp.prefixo_mapa
                          ? ` (${emp.prefixo_mapa})`
                          : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex w-full flex-col gap-1.5">
              <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                Turno <span className="req">*</span>
              </Label>
              <Select
                value={turno ?? ''}
                onValueChange={(v) => setTurno(v ?? '')}
              >
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

            <div className="grid grid-cols-2 items-start gap-3">
              <FormField
                label="INÍCIO DO PLANTÃO"
                name="inicio"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                maxLength={5}
                value={inicioHHMM ?? ''}
                onChange={(e) => setInicioHHMM(maskHHMM(e.target.value))}
                className="bg-white"
              />
              <FormField
                label="FIM DO PLANTÃO"
                name="fim"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                maxLength={5}
                value={fimHHMM ?? ''}
                onChange={(e) => setFimHHMM(maskHHMM(e.target.value))}
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
              onClick={onCancelar}
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
