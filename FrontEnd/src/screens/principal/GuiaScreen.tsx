import { useCallback, useEffect, useRef, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import {

  createGuia,

  deleteGuia,

  getGuiaByNumero,

  updateGuia,

  type GuiaRecord,

} from '@/api/guia';

import { getCadastros } from '@/api/cadastros';

import {

  ButtonToolbar,

  IconDeletar,

  IconNovo,

  IconPesquisar,

  IconSalvar,

} from '@/components/shared/ButtonToolbar';

import { AppDialog } from '@/components/shared/AppDialog';

import { FormField } from '@/components/forms/FormField';

import { DatePickerField } from '@/components/forms/DatePickerField';

import { PageHeader } from '@/components/shared/PageHeader';

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

import type { CadastrosMestres, LinhaCadastro } from '@/types/cadastros';

import { parseDateBR, toDateBR } from '@/utils/appFormat';

import { onlyDigits } from '@/utils/validation';



const BG = '#B9C8D4';

const MSG_CADASTRO_OK = 'Guia cadastrada com sucesso!';

const MSG_CADASTRO_ERRO = 'Não foi possível cadastrar a guia!';

const MSG_EXCLUSAO_OK = 'Guia excluída com sucesso.';



type GuiaModo = 'idle' | 'edicao';



const fieldClass =

  'h-10 rounded-lg bg-white text-sm shadow-none border-slate-400';

const halfFieldClass = cn(fieldClass, 'w-full max-w-none');

const selectTriggerClass = cn(fieldClass, 'h-10 w-full text-sm');

const labelClass =

  'flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900';



function maskHHMM(raw: string): string {

  const digits = raw.replace(/\D/g, '').slice(0, 4);

  if (digits.length <= 2) return digits;

  return `${digits.slice(0, 2)}:${digits.slice(2)}`;

}



function formatLinhaLabel(l: LinhaCadastro): string {

  const cod =

    l.codigo_linha != null && Number.isFinite(Number(l.codigo_linha))

      ? String(Math.trunc(Number(l.codigo_linha)))

      : String(l.id_linha);

  return l.descricao ? `${cod}-${l.descricao}` : cod;

}



function normalizeNrGuia(raw: string): string {

  return raw.replace(/\D/g, '');

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



function limparFormulario() {

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



type FormState = ReturnType<typeof limparFormulario>;



function montarPayload(state: FormState) {

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



function validarFormulario(payload: ReturnType<typeof montarPayload>): string | null {

  if (!payload.numero.trim()) return 'Informe o NR(Guia).';

  if (!parseDateBR(payload.data.trim())) return 'Data inválida.';

  if (payload.horario_pegada && !/^\d{2}:\d{2}$/.test(payload.horario_pegada)) {

    return 'INÍCIO(JORNADA) inválido.';

  }

  if (payload.horario_largada && !/^\d{2}:\d{2}$/.test(payload.horario_largada)) {

    return 'FIM(JORNADA) inválido.';

  }

  if (payload.carro && !/^\d{1,5}$/.test(payload.carro)) {

    return 'Carro deve conter até 5 dígitos numéricos.';

  }

  if (payload.motorista && !/^\d{1,5}$/.test(payload.motorista)) {

    return 'Motorista deve conter até 5 dígitos numéricos.';

  }

  return null;

}



/** Tela Guia — RF-29..RF-51. */

export function GuiaScreen() {

  const navigate = useNavigate();

  useScreenBg(BG);

  const nrGuiaRef = useRef<HTMLInputElement>(null);



  const [loading, setLoading] = useState(true);

  const [busy, setBusy] = useState(false);

  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);

  const [modo, setModo] = useState<GuiaModo>('idle');

  const [novoDesabilitado, setNovoDesabilitado] = useState(false);

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



  const camposHabilitados = modo === 'edicao' && !busy;

  const salvarHabilitado = modo === 'edicao' && !busy;

  const deletarHabilitado = modo === 'edicao' && !busy;

  const novoHabilitado = !busy && !novoDesabilitado;

  const pesquisarHabilitado = !busy;



  const observacaoFieldClass = cn(fieldClass, 'w-full max-w-none resize-none py-2');



  const aplicarFormulario = useCallback((values: FormState) => {

    setNrGuia(values.nrGuia);

    setDataGuia(values.dataGuia);

    setIdEmpresa(values.idEmpresa);

    setIdLinha(values.idLinha);

    setIdTurno(values.idTurno);

    setCarro(values.carro);

    setMotorista(values.motorista);

    setHorarioPegada(values.horarioPegada);

    setHorarioLargada(values.horarioLargada);

    setRoletaInicial(values.roletaInicial);

    setRoletaFinal(values.roletaFinal);

    setRoleta2Inicial(values.roleta2Inicial);

    setRoleta2Final(values.roleta2Final);

    setObservacao(values.observacao);

  }, []);



  const aplicarGuia = useCallback(

    (guia: GuiaRecord) => {

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

      setModo('edicao');

      setNovoDesabilitado(false);

    },

    [aplicarFormulario],

  );



  const resetIdle = useCallback(() => {

    setModo('idle');

    setNovoDesabilitado(false);

    setIdGuia(null);

    aplicarFormulario(limparFormulario());

  }, [aplicarFormulario]);



  const carregarCadastros = useCallback(async () => {

    setLoading(true);

    try {

      const { response, data } = await getCadastros();

      if (response.ok && data && 'ok' in data && data.ok === true) {

        setCadastros(data.cadastros);

      } else {

        setCadastros(null);

      }

    } catch {

      setCadastros(null);

    } finally {

      setLoading(false);

    }

  }, []);



  useEffect(() => {

    void carregarCadastros();

  }, [carregarCadastros]);



  const pesquisarPorNumero = async (numero: string) => {

    const alvo = numero.trim();

    if (!alvo) {

      setInfoMsg('Informe o número da guia.');

      return;

    }

    setBusy(true);

    try {

      const { response, data } = await getGuiaByNumero(alvo);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        const msg =

          data && 'mensagem' in data && data.mensagem

            ? data.mensagem

            : 'Guia não encontrada.';

        setInfoMsg(msg);

        return;

      }

      aplicarGuia(data.guia);

      setPesquisarOpen(false);

      setPesquisarNumero('');

    } catch {

      setInfoMsg('Falha de comunicação com a API.');

    } finally {

      setBusy(false);

    }

  };



  const abrirPesquisar = () => {

    setPesquisarNumero('');

    setPesquisarOpen(true);

  };



  const novo = () => {

    setModo('edicao');

    setNovoDesabilitado(false);

    setIdGuia(null);

    aplicarFormulario({

      ...limparFormulario(),

      dataGuia: dataHojeBR(),

    });

    window.setTimeout(() => nrGuiaRef.current?.focus(), 0);

  };



  const salvar = async () => {

    if (busy || modo !== 'edicao') return;

    const body = montarPayload(formState);

    const erroLocal = validarFormulario(body);

    if (erroLocal) {

      setInfoMsg(erroLocal);

      return;

    }



    setBusy(true);

    try {

      if (idGuia != null) {

        const { response, data } = await updateGuia(idGuia, body);

        if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

          const msg =

            data && 'mensagem' in data && data.mensagem

              ? data.mensagem

              : 'Não foi possível salvar a guia.';

          setInfoMsg(msg);

          return;

        }

        aplicarGuia(data.guia);

        setInfoMsg(data.mensagem ?? 'Guia atualizada com sucesso.');

        return;

      }



      const { response, data } = await createGuia(body);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        setInfoMsg(MSG_CADASTRO_ERRO);

        return;

      }

      aplicarGuia(data.guia);

      setNovoDesabilitado(true);

      setInfoMsg(data.mensagem ?? MSG_CADASTRO_OK);

    } catch {

      setInfoMsg(idGuia == null ? MSG_CADASTRO_ERRO : 'Falha de comunicação com a API.');

    } finally {

      setBusy(false);

    }

  };



  const deletar = async () => {

    if (busy || modo !== 'edicao') return;

    if (idGuia == null) {

      setInfoMsg('Nenhuma guia carregada para excluir.');

      return;

    }

    setBusy(true);

    try {

      const { response, data } = await deleteGuia(idGuia);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        const msg =

          data && 'mensagem' in data && data.mensagem

            ? data.mensagem

            : 'Não foi possível excluir a guia.';

        setInfoMsg(msg);

        return;

      }

      resetIdle();

      setInfoMsg(data.mensagem ?? MSG_EXCLUSAO_OK);

    } catch {

      setInfoMsg('Falha de comunicação com a API.');

    } finally {

      setBusy(false);

    }

  };



  const toolbarActions = [

    {

      key: 'novo',

      label: 'Novo',

      icon: <IconNovo />,

      onClick: () => novo(),

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

      onClick: () => abrirPesquisar(),

      disabled: !pesquisarHabilitado,

    },

  ];



  if (loading) {

    return (

      <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">

        <PageHeader title="GUIA" onBack={() => navigate('/principal')} />

        <p className="p-6 text-center text-sm font-medium text-slate-700">Carregando…</p>

      </div>

    );

  }



  return (

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

              value={idEmpresa || undefined}

              onValueChange={setIdEmpresa}

              disabled={!camposHabilitados}

            >

              <SelectTrigger className={selectTriggerClass}>

                <SelectValue placeholder="Selecione" />

              </SelectTrigger>

              <SelectContent>

                {(cadastros?.empresas ?? []).map((e) => (

                  <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>

                    {e.descricao}

                  </SelectItem>

                ))}

              </SelectContent>

            </Select>

          </div>



          <div className="flex w-full flex-col gap-1.5">

            <Label className={labelClass}>Linha</Label>

            <Select

              value={idLinha || undefined}

              onValueChange={setIdLinha}

              disabled={!camposHabilitados}

            >

              <SelectTrigger className={selectTriggerClass}>

                <SelectValue placeholder="Selecione" />

              </SelectTrigger>

              <SelectContent>

                {(cadastros?.linhas ?? []).map((l) => (

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

              value={idTurno || undefined}

              onValueChange={setIdTurno}

              disabled={!camposHabilitados}

            >

              <SelectTrigger className={selectTriggerClass}>

                <SelectValue placeholder="Selecione" />

              </SelectTrigger>

              <SelectContent>

                {(cadastros?.turnos ?? []).map((t) => (

                  <SelectItem key={t.id_turno} value={String(t.id_turno)}>

                    {t.descricao}

                  </SelectItem>

                ))}

              </SelectContent>

            </Select>

          </div>



          <div className="grid grid-cols-2 gap-3">

            <FormField

              label="Carro"

              name="carro"

              type="tel"

              inputMode="numeric"

              value={carro}

              onChange={(e) => setCarro(onlyDigits(e.target.value, 5))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

            <FormField

              label="Motorista"

              name="motorista"

              type="tel"

              inputMode="numeric"

              value={motorista}

              onChange={(e) => setMotorista(onlyDigits(e.target.value, 5))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

          </div>



          <div className="grid grid-cols-2 gap-3">

            <FormField

              label="INÍCIO(JORNADA)"

              name="horario_pegada"

              placeholder="HH:MM"

              value={horarioPegada}

              onChange={(e) => setHorarioPegada(maskHHMM(e.target.value))}

              inputMode="numeric"

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

            <FormField

              label="FIM(JORNADA)"

              name="horario_largada"

              placeholder="HH:MM"

              value={horarioLargada}

              onChange={(e) => setHorarioLargada(maskHHMM(e.target.value))}

              inputMode="numeric"

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

          </div>



          <div className="grid grid-cols-2 gap-3">

            <FormField

              label="ROLETA 01(INICIAL)"

              name="roleta01_inicial"

              type="tel"

              inputMode="numeric"

              value={roletaInicial}

              onChange={(e) => setRoletaInicial(onlyDigits(e.target.value))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

            <FormField

              label="ROLETA 01(FINAL)"

              name="roleta01_final"

              type="tel"

              inputMode="numeric"

              value={roletaFinal}

              onChange={(e) => setRoletaFinal(onlyDigits(e.target.value))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

          </div>



          <div className="grid grid-cols-2 gap-3">

            <FormField

              label="ROLETA 02(INICIAL)"

              name="roleta2_inicial"

              type="tel"

              inputMode="numeric"

              value={roleta2Inicial}

              onChange={(e) => setRoleta2Inicial(onlyDigits(e.target.value))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

            <FormField

              label="ROLETA 02(FINAL)"

              name="roleta2_final"

              type="tel"

              inputMode="numeric"

              value={roleta2Final}

              onChange={(e) => setRoleta2Final(onlyDigits(e.target.value))}

              className={cn(fieldClass, 'w-full max-w-none')}

              disabled={!camposHabilitados}

            />

          </div>



          <div className="flex w-full flex-col gap-1.5">

            <Label htmlFor="observacao" className={labelClass}>

              Observação

            </Label>

            <textarea

              id="observacao"

              name="observacao"

              value={observacao}

              onChange={(e) => setObservacao(e.target.value.slice(0, 150))}

              maxLength={150}

              rows={1}

              disabled={!camposHabilitados}

              className={cn(

                observacaoFieldClass,

                'w-full border border-slate-400 px-3 py-2 text-slate-900 placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60',

              )}

            />

          </div>

        </div>



        <div className="mt-auto">

          <Separator className="bg-black" />

          <div className="pt-3">

            <ButtonToolbar actions={toolbarActions} />

          </div>

        </div>

      </div>



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

              Número da guia

            </Label>

            <Input

              id="pesquisa_nr_guia"

              inputMode="numeric"

              autoComplete="off"

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



      <AppDialog

        open={infoMsg !== null}

        message={infoMsg ?? ''}

        confirmLabel="OK"

        onConfirm={() => setInfoMsg(null)}

      />

    </div>

  );

}


