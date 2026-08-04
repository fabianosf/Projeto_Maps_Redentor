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
import { me } from '@/api/auth';
import { createMapa, getCadastros, getMapa, updateMapa } from '@/api/mapa';
import { DatePickerField } from '@/components/forms/DatePickerField';
import { FormField } from '@/components/forms/FormField';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { CadastrosMestres, MapaHeaderPayload } from '@/types/mapa';
import {
  apiErrorMessage,
  brToYmd,
  combineDateAndTime,
  formatHora,
  isValidHHMM,
  toDateBR,
  todayBR,
  parseDateBR,
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
  // aceita "1", "01", "1°", "2°" etc.
  const num = t.replace(/\D/g, '');
  if (num) {
    const byCode = TURNO_OPCOES.find((o) => o.endsWith(num.padStart(2, '0')));
    if (byCode) return byCode;
  }
  return TURNO_OPCOES[0];
}

/**
 * Tela 05 — Cadastro de Mapa (formulário MAPAS).
 */
export function MapasScreen() {
  const navigate = useNavigate();
  const { idRegistro: idParam } = useParams();
  const idRegistro = idParam ? Number(idParam) : null;
  const isEdit = idRegistro != null && Number.isFinite(idRegistro);
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

  /** Resolve label da empresa → id_empresa (API / codigo). */
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

  /** Resolve label do turno → id_turno (API / codigo). */
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

  const goLista = () => navigate('/lista-mapa', { replace: true });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [meRes, cadRes] = await Promise.all([me(), getCadastros()]);
        if (cancelled) return;

        if (meRes.response.ok && meRes.data && 'ok' in meRes.data && meRes.data.ok === true) {
          setMatricula(String(meRes.data.usuario.matricula ?? ''));
        }

        let cad: CadastrosMestres | null = null;
        if (
          cadRes.response.ok &&
          cadRes.data &&
          'ok' in cadRes.data &&
          cadRes.data.ok === true
        ) {
          cad = cadRes.data.cadastros;
          setCadastros(cad);
        } else {
          toast.error(apiErrorMessage(cadRes.data, 'Falha ao carregar cadastros.'));
        }

        if (isEdit && idRegistro != null) {
          const mapRes = await getMapa(idRegistro);
          if (cancelled) return;
          if (
            !mapRes.response.ok ||
            !mapRes.data ||
            !('ok' in mapRes.data) ||
            mapRes.data.ok !== true
          ) {
            toast.error(apiErrorMessage(mapRes.data, 'MAPA não encontrado.'));
            goLista();
            return;
          }
          const m = mapRes.data.mapa;
          setDataBR(toDateBR(m.data) || todayBR());
          setInicioHHMM(formatHora(m.inicio_jornada_des).replace('—', ''));
          setFimHHMM(formatHora(m.fim_jornada_des).replace('—', ''));
          setIdLinha(toId(m.id_linha));
          setEmpresa(normalizeEmpresaLabel(String(m.empresa ?? EMPRESA_OPCOES[0])));
          setTurno(normalizeTurnoLabel(String(m.turno ?? TURNO_OPCOES[0])));
          const linha = cad?.linhas.find((l) => toId(l.id_linha) === toId(m.id_linha));
          if (linha) {
            setCodigoLinha(String(linha.codigo_linha ?? linha.descricao ?? ''));
            if (linha.empresa) setEmpresa(normalizeEmpresaLabel(String(linha.empresa)));
          }
        } else {
          setDataBR(todayBR());
          setEmpresa(EMPRESA_OPCOES[0]); // Futuro
          setTurno(TURNO_OPCOES[0]); // TURNO 01
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
    // FIM DE JORNADA é opcional (aceita vazio)
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
    if (!idEmpresaNum) {
      toast.error('Selecione a empresa.');
      return;
    }
    if (!idTurnoNum) {
      toast.error('O campo Turno é obrigatório.');
      return;
    }

    let linhaId = idLinha;
    if (!linhaId) {
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

    const payload: Record<string, unknown> = {
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
    // Só envia id_linha quando já existe no cadastro (evita null rejeitado pelo backend antigo)
    if (linhaId) {
      payload.id_linha = Number(linhaId);
    }

    setBusy(true);
    try {
      const body = payload as MapaHeaderPayload;
      const { response, data: res } =
        isEdit && idRegistro != null
          ? await updateMapa(idRegistro, body)
          : await createMapa(body);

      if (!response.ok || !res || !('ok' in res) || res.ok !== true) {
        toast.error(apiErrorMessage(res, 'Falha ao salvar MAPA.'));
        return;
      }
      toast.success(isEdit ? 'MAPA atualizado com sucesso.' : 'MAPA cadastrado com sucesso.');
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
        <PageHeader title="MAPA" onBack={goLista} />
        <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
      <PageHeader
        title="MAPA"
        onBack={goLista}
        rightSlot={
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Abrir registros"
            onClick={() => {
              if (!isEdit || idRegistro == null) {
                toast.message('Salve o MAPA antes de abrir os registros.');
                return;
              }
              navigate(`/mapas/${idRegistro}/registros`);
            }}
            className="h-9 w-9 rounded border border-white/70 text-white hover:bg-white/10"
          >
            <ClipboardList className="h-5 w-5" strokeWidth={2.25} />
          </Button>
        }
      />

      <form
        className="page-body bg-[#B9C8D4]"
        onSubmit={(e) => void onSubmit(e)}
        autoComplete="off"
      >
        <div className="field-stack">
          {/* Matrícula + Data: mesma altura de label e input */}
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
  );
}
