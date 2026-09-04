import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import {
  createGuia,
  deleteGuia,
  getGuiaByNumero,
  updateGuia,
} from '@/api/guia';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { DatePickerField } from '@/components/forms/DatePickerField';
import {
  ButtonToolbar,
  IconDeletar,
  IconNovo,
  IconPesquisar,
  IconSalvar,
} from '@/components/shared/ButtonToolbar';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useScreenBg } from '@/hooks/useScreenBg';
import { cn } from '@/lib/utils';
import type { CadastrosMestres, LinhaCadastro } from '@/types/cadastro';
import type { Guia, GuiaPayload } from '@/types/guia';
import { parseDateBR, toDateBR } from '@/utils/appFormat';
import { onlyDigits } from '@/utils/validation';

const BG = '#B9C8D4';
const MSG_CADASTRO_OK = 'Guia cadastrada com sucesso!';
/** Sentinel: Radix trata value="" como “sem value” (uncontrolled). */
const SELECT_EMPTY = '__empty__';

function toSelectValue(v: string): string {
  return v === '' ? SELECT_EMPTY : v;
}

function fromSelectValue(v: string): string {
  return v === SELECT_EMPTY ? '' : v;
}
const MSG_CADASTRO_ERRO = 'Não foi possível cadastrar a guia!';
const MSG_EXCLUSAO_OK = 'Guia excluída com sucesso!';
const OBS_MAX = 150;
const NR_MAX = 15;

/** idle | include (Novo) | edit (pesquisado / após salvar) */
type GuiaModo = 'idle' | 'include' | 'edit';

const fieldClass = 'h-10 rounded-lg bg-white text-sm shadow-none border-slate-400';
const halfFieldClass = cn(fieldClass, 'w-full max-w-none');
const selectTriggerClass = cn(fieldClass, 'h-10 w-full text-sm');
const labelClass =
  'flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900';

function maskHHMM(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

/** HH:MM estrito com hora/minuto válidos. */
function isValidHHMM(value: string): boolean {
  if (!/^\d{2}:\d{2}$/.test(value)) return false;
  const h = Number(value.slice(0, 2));
  const m = Number(value.slice(3, 5));
  return h >= 0 && h <= 23 && m >= 0 && m <= 59;
}

function formatLinhaLabel(l: LinhaCadastro): string {
  const cod =
    l.codigo_linha != null && Number.isFinite(Number(l.codigo_linha))
      ? String(Math.trunc(Number(l.codigo_linha)))
      : String(l.id_linha);
  return l.descricao ? `${cod}-${l.descricao}` : cod;
}

function normalizeNrGuia(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, NR_MAX);
}

function dataHojeBR(): string {
  const hoje = new Date();
  const dd = String(hoje.getDate()).padStart(2, '0');
  const mm = String(hoje.getMonth() + 1).padStart(2, '0');
  const yyyy = hoje.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function extractHHMM(value: string | null | undefined): string {
  if (!value) return '';
  const m = String(value).match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : '';
}

function emptyForm() {
  return {
    nrGuia: '',
    dataGuia: '',
    idEmpresa: '',
    idLinha: '',
    idTurno: '',
    carro: '',
    motorista: '',
    horarioPegada: '',
    horarioLargada: '',
    roletaInicial: '',
    roletaFinal: '',
    roleta2Inicial: '',
    roleta2Final: '',
    observacao: '',
  };
}

type FormState = ReturnType<typeof emptyForm>;

function montarPayload(state: FormState): GuiaPayload {
  return {
    numero: state.nrGuia.trim(),
    data: state.dataGuia.trim(),
    id_empresa: state.idEmpresa ? Number(state.idEmpresa) : null,
    id_linha: state.idLinha ? Number(state.idLinha) : null,
    id_turno: state.idTurno ? Number(state.idTurno) : null,
    carro: state.carro.trim(),
    motorista: state.motorista.trim(),
    horario_pegada: state.horarioPegada.trim(),
    horario_largada: state.horarioLargada.trim(),
    roleta01_inicial: state.roletaInicial ? Number(state.roletaInicial) : null,
    roleta01_final: state.roletaFinal ? Number(state.roletaFinal) : null,
    roleta2_inicial: state.roleta2Inicial ? Number(state.roleta2Inicial) : null,
    roleta2_final: state.roleta2Final ? Number(state.roleta2Final) : null,
    observacao: state.observacao.trim(),
  };
}

function validarFormulario(payload: GuiaPayload): string | null {
  if (!payload.numero.trim()) return 'Informe o NR(Guia).';
  if (!parseDateBR(payload.data.trim())) return 'Data inválida.';
  const ini = payload.horario_pegada ?? '';
  const fim = payload.horario_largada ?? '';
  if (ini && !isValidHHMM(ini)) return 'INÍCIO(JORNADA) inválido.';
  if (fim && !isValidHHMM(fim)) return 'FIM(JORNADA) inválido.';
  const carro = payload.carro ?? '';
  const motorista = payload.motorista ?? '';
  if (carro && !/^\d{1,5}$/.test(carro)) {
    return 'Carro deve conter até 5 dígitos numéricos.';
  }
  if (motorista && !/^\d{1,5}$/.test(motorista)) {
    return 'Motorista deve conter até 5 dígitos numéricos.';
  }
  if ((payload.observacao ?? '').length > OBS_MAX) {
    return `Observação deve ter no máximo ${OBS_MAX} caracteres.`;
  }
  return null;
}

function apiMsg(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) {
    return err.body.mensagem || fallback;
  }
  return fallback;
}

/** Tela 08 — Guia (RF-29..RF-51). */
export function GuiaScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);
  const nrGuiaRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [modo, setModo] = useState<GuiaModo>('idle');
  const [idGuia, setIdGuia] = useState<number | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [pesquisarOpen, setPesquisarOpen] = useState(false);
  const [pesquisarNumero, setPesquisarNumero] = useState('');

  const [nrGuia, setNrGuia] = useState('');
  const [dataGuia, setDataGuia] = useState('');
  const [idEmpresa, setIdEmpresa] = useState('');
  const [idLinha, setIdLinha] = useState('');
  const [idTurno, setIdTurno] = useState('');
  const [carro, setCarro] = useState('');
  const [motorista, setMotorista] = useState('');
  const [horarioPegada, setHorarioPegada] = useState('');
  const [horarioLargada, setHorarioLargada] = useState('');
  const [roletaInicial, setRoletaInicial] = useState('');
  const [roletaFinal, setRoletaFinal] = useState('');
  const [roleta2Inicial, setRoleta2Inicial] = useState('');
  const [roleta2Final, setRoleta2Final] = useState('');
  const [observacao, setObservacao] = useState('');

  const formState: FormState = {
    nrGuia,
    dataGuia,
    idEmpresa,
    idLinha,
    idTurno,
    carro,
    motorista,
    horarioPegada,
    horarioLargada,
    roletaInicial,
    roletaFinal,
    roleta2Inicial,
    roleta2Final,
    observacao,
  };

  const camposHabilitados = (modo === 'include' || modo === 'edit') && !busy;
  const salvarHabilitado = (modo === 'include' || modo === 'edit') && !busy;
  const deletarHabilitado = modo === 'edit' && idGuia != null && !busy;
  const novoHabilitado = !busy;
  const pesquisarHabilitado = !busy;

  const aplicarFormulario = useCallback((values: FormState) => {
    setNrGuia(values.nrGuia ?? '');
    setDataGuia(values.dataGuia ?? '');
    setIdEmpresa(values.idEmpresa ?? '');
    setIdLinha(values.idLinha ?? '');
    setIdTurno(values.idTurno ?? '');
    setCarro(values.carro ?? '');
    setMotorista(values.motorista ?? '');
    setHorarioPegada(values.horarioPegada ?? '');
    setHorarioLargada(values.horarioLargada ?? '');
    setRoletaInicial(values.roletaInicial ?? '');
    setRoletaFinal(values.roletaFinal ?? '');
    setRoleta2Inicial(values.roleta2Inicial ?? '');
    setRoleta2Final(values.roleta2Final ?? '');
    setObservacao(values.observacao ?? '');
  }, []);

  const aplicarGuia = useCallback(
    (guia: Guia, nextModo: GuiaModo = 'edit') => {
      setIdGuia(guia.id_guia);
      aplicarFormulario({
        nrGuia: guia.numero ?? '',
        dataGuia: toDateBR(guia.hor_ini ?? guia.hor_fim ?? guia.data ?? undefined),
        idEmpresa: guia.id_empresa != null ? String(guia.id_empresa) : '',
        idLinha: guia.id_linha != null ? String(guia.id_linha) : '',
        idTurno: guia.id_turno != null ? String(guia.id_turno) : '',
        carro: guia.numero_frota ?? '',
        motorista: guia.matricula_motorista ?? '',
        horarioPegada: extractHHMM(guia.hor_ini),
        horarioLargada: extractHHMM(guia.hor_fim),
        roletaInicial: guia.roleta01_ini != null ? String(guia.roleta01_ini) : '',
        roletaFinal: guia.roleta01_fim != null ? String(guia.roleta01_fim) : '',
        roleta2Inicial: guia.roleta2_ini != null ? String(guia.roleta2_ini) : '',
        roleta2Final: guia.roleta2_fim != null ? String(guia.roleta2_fim) : '',
        observacao: guia.observacao ?? '',
      });
      setModo(nextModo);
    },
    [aplicarFormulario],
  );

  const resetIdle = useCallback(() => {
    setModo('idle');
    setIdGuia(null);
    aplicarFormulario(emptyForm());
  }, [aplicarFormulario]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getCadastros();
        if (!cancelled) setCadastros(data.cadastros);
      } catch {
        if (!cancelled) setCadastros(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const linhasFiltradas = (cadastros?.linhas ?? []).filter((l) =>
    idEmpresa ? String(l.id_empresa) === idEmpresa : true,
  );

  const novo = () => {
    setIdGuia(null);
    aplicarFormulario({ ...emptyForm(), dataGuia: dataHojeBR() });
    setModo('include');
    window.setTimeout(() => nrGuiaRef.current?.focus(), 0);
  };

  const pesquisarPorNumero = async (numero: string) => {
    const alvo = numero.trim();
    if (!alvo) {
      setInfoMsg('Informe o número da guia.');
      return;
    }
    setBusy(true);
    try {
      const data = await getGuiaByNumero(alvo);
      aplicarGuia(data.guia, 'edit');
      setPesquisarOpen(false);
      setPesquisarNumero('');
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Guia não encontrada.'));
    } finally {
      setBusy(false);
    }
  };

  const salvar = async () => {
    if (busy || (modo !== 'include' && modo !== 'edit')) return;
    const body = montarPayload(formState);
    const erroLocal = validarFormulario(body);
    if (erroLocal) {
      setInfoMsg(erroLocal);
      return;
    }

    setBusy(true);
    try {
      if (idGuia != null) {
        const data = await updateGuia(idGuia, body);
        aplicarGuia(data.guia, 'edit');
        setInfoMsg(data.mensagem ?? 'Guia atualizada com sucesso.');
        return;
      }
      const data = await createGuia(body);
      aplicarGuia(data.guia, 'edit');
      setInfoMsg(data.mensagem ?? MSG_CADASTRO_OK);
    } catch (err) {
      if (idGuia == null) {
        setInfoMsg(MSG_CADASTRO_ERRO);
      } else {
        setInfoMsg(apiMsg(err, 'Não foi possível salvar a guia.'));
      }
    } finally {
      setBusy(false);
    }
  };

  const deletar = async () => {
    if (!deletarHabilitado || idGuia == null) return;
    setBusy(true);
    try {
      await deleteGuia(idGuia);
      resetIdle();
      setInfoMsg(MSG_EXCLUSAO_OK);
    } catch (err) {
      setInfoMsg(apiMsg(err, 'Não foi possível excluir a guia.'));
    } finally {
      setBusy(false);
    }
  };

  const toolbarActions = [
    {
      key: 'novo',
      label: 'Novo',
      icon: <IconNovo />,
      onClick: novo,
      disabled: !novoHabilitado,
    },
    {
      key: 'salvar',
      label: 'Salvar',
      icon: <IconSalvar />,
      onClick: () => void salvar(),
      disabled: !salvarHabilitado,
    },
    {
      key: 'deletar',
      label: 'Deletar',
      icon: <IconDeletar />,
      onClick: () => void deletar(),
      disabled: !deletarHabilitado,
    },
    {
      key: 'pesquisar',
      label: 'Pesquisar',
      icon: <IconPesquisar />,
      onClick: () => {
        setPesquisarNumero('');
        setPesquisarOpen(true);
      },
      disabled: !pesquisarHabilitado,
    },
  ];

  if (loading) {
    return (
      <AppShell className="bg-[#B9C8D4]">
        <div className="page min-h-dvh bg-[#B9C8D4]">
          <PageHeader title="GUIA" onBack={() => navigate('/principal')} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-[#B9C8D4]">
      <div className="page flex min-h-dvh flex-col bg-[#B9C8D4] text-slate-900">
        <PageHeader title="GUIA" onBack={() => navigate('/principal')} />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-3">
          <div className="field-stack gap-3 rounded-xl border-2 border-slate-500/40 bg-white/50 p-3">
            <div className="grid grid-cols-2 gap-3">
              <FormField
                ref={nrGuiaRef}
                label="NR(Guia)"
                name="nr_guia"
                type="tel"
                inputMode="numeric"
                autoComplete="off"
                maxLength={NR_MAX}
                placeholder="Digite ou leia o código de barras"
                value={nrGuia}
                onChange={(e) => setNrGuia(normalizeNrGuia(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
              <DatePickerField
                label="Data"
                name="data_guia"
                value={dataGuia}
                onChange={setDataGuia}
                iconBesideLabel
                inputClassName="h-10 text-sm shadow-none"
                disabled={!camposHabilitados}
              />
            </div>

            <div className="flex w-full flex-col gap-1.5">
              <Label className={labelClass}>Empresa</Label>
              <Select
                value={toSelectValue(idEmpresa)}
                onValueChange={(v) => {
                  setIdEmpresa(fromSelectValue(v));
                  setIdLinha('');
                }}
                disabled={!camposHabilitados}
              >
                <SelectTrigger className={selectTriggerClass}>
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                    Selecione
                  </SelectItem>
                  {(cadastros?.empresas ?? []).map((e) => (
                    <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>
                      {e.descricao}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex w-full flex-col gap-1.5">
                <Label className={labelClass}>Linha</Label>
                <Select
                  value={toSelectValue(idLinha)}
                  onValueChange={(v) => setIdLinha(fromSelectValue(v))}
                  disabled={!camposHabilitados}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                      Selecione
                    </SelectItem>
                    {linhasFiltradas.map((l) => (
                      <SelectItem key={l.id_linha} value={String(l.id_linha)}>
                        {formatLinhaLabel(l)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex w-full flex-col gap-1.5">
                <Label className={labelClass}>Turno</Label>
                <Select
                  value={toSelectValue(idTurno)}
                  onValueChange={(v) => setIdTurno(fromSelectValue(v))}
                  disabled={!camposHabilitados}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SELECT_EMPTY} disabled className="hidden">
                      Selecione
                    </SelectItem>
                    {(cadastros?.turnos ?? []).map((t) => (
                      <SelectItem key={t.id_turno} value={String(t.id_turno)}>
                        {t.descricao}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Carro"
                name="carro"
                type="tel"
                inputMode="numeric"
                maxLength={5}
                value={carro}
                onChange={(e) => setCarro(onlyDigits(e.target.value, 5))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
              <FormField
                label="Motorista"
                name="motorista"
                type="tel"
                inputMode="numeric"
                maxLength={5}
                value={motorista}
                onChange={(e) => setMotorista(onlyDigits(e.target.value, 5))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Início(Jornada)"
                name="hor_ini"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                value={horarioPegada}
                onChange={(e) => setHorarioPegada(maskHHMM(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
              <FormField
                label="Fim(Jornada)"
                name="hor_fim"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                value={horarioLargada}
                onChange={(e) => setHorarioLargada(maskHHMM(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Roleta 01 inicial"
                name="roleta01_ini"
                type="tel"
                inputMode="numeric"
                value={roletaInicial}
                onChange={(e) => setRoletaInicial(onlyDigits(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
              <FormField
                label="Roleta 01 final"
                name="roleta01_fim"
                type="tel"
                inputMode="numeric"
                value={roletaFinal}
                onChange={(e) => setRoletaFinal(onlyDigits(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Roleta 02 inicial"
                name="roleta2_ini"
                type="tel"
                inputMode="numeric"
                value={roleta2Inicial}
                onChange={(e) => setRoleta2Inicial(onlyDigits(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
              <FormField
                label="Roleta 02 final"
                name="roleta2_fim"
                type="tel"
                inputMode="numeric"
                value={roleta2Final}
                onChange={(e) => setRoleta2Final(onlyDigits(e.target.value))}
                className={halfFieldClass}
                disabled={!camposHabilitados}
              />
            </div>

            <div className="flex w-full flex-col gap-1.5">
              <Label className={labelClass} htmlFor="observacao_guia">
                Observação
              </Label>
              <textarea
                id="observacao_guia"
                name="observacao"
                rows={3}
                maxLength={OBS_MAX}
                value={observacao}
                onChange={(e) => setObservacao(e.target.value.slice(0, OBS_MAX))}
                disabled={!camposHabilitados}
                className={cn(
                  fieldClass,
                  'min-h-[4.5rem] w-full resize-y px-3 py-2 text-sm disabled:opacity-60',
                )}
              />
            </div>
          </div>

          <Separator className="bg-black" />
          <ButtonToolbar actions={toolbarActions} />
        </div>

        <AlertDialog
          open={infoMsg !== null}
          message={infoMsg ?? ''}
          onConfirm={() => setInfoMsg(null)}
        />

        <Dialog open={pesquisarOpen} onOpenChange={setPesquisarOpen}>
          <DialogContent className="max-w-[340px] border-slate-400/50 bg-[#B9C8D4] p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide text-slate-900">
                Pesquisar guia
              </DialogTitle>
            </DialogHeader>
            <div className="mt-2">
              <Label
                htmlFor="pesquisa_nr_guia"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                NR(Guia)
              </Label>
              <Input
                id="pesquisa_nr_guia"
                inputMode="numeric"
                autoComplete="off"
                maxLength={NR_MAX}
                value={pesquisarNumero}
                onChange={(e) => setPesquisarNumero(normalizeNrGuia(e.target.value))}
                className="h-12 rounded-lg border-slate-400 bg-white text-base text-slate-900"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    void pesquisarPorNumero(pesquisarNumero);
                  }
                }}
              />
            </div>
            <DialogFooter className="mt-5">
              <Button
                type="button"
                className="w-full"
                disabled={busy || !pesquisarNumero.trim()}
                onClick={() => void pesquisarPorNumero(pesquisarNumero)}
              >
                OK
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
