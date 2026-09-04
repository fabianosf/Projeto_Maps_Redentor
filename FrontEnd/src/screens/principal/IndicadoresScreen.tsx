import { useCallback, useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import { me } from '@/api/auth';

import {
  getIndicadoresVinculoPerfil,
  listPerfisIndicadoresConfig,
  saveIndicadoresVinculoPerfil,
} from '@/api/indicadoresConfig';

import { AppDialog } from '@/components/shared/AppDialog';

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

import { Separator } from '@/components/ui/separator';

import {

  Table,

  TableBody,

  TableCell,

  TableHead,

  TableHeader,

  TableRow,

} from '@/components/ui/table';

import { useScreenBg } from '@/hooks/useScreenBg';

import { actionBtn3dMd } from '@/lib/actionBtn3d';

import type { IndicadorVinculoItem } from '@/types/indicadores';

import { apiErrorMessage } from '@/utils/appFormat';
import { canAccessConfiguracao } from '@/utils/perfilAccess';



const BG = '#B9C8D4';



const labelClass =

  'flex h-5 items-center font-sans text-[12px] font-normal uppercase leading-none tracking-wide text-slate-600';



const selectTriggerClass =

  'h-10 w-full rounded-lg border-slate-400 bg-white font-sans text-[15px] font-normal text-slate-900';



const tableHeadClass =

  'font-sans font-normal uppercase tracking-wide text-slate-700';



const tableSiglaClass = 'font-sans text-[13px] font-bold text-slate-900';



const tableDetalheClass = 'font-sans text-[13px] font-normal text-slate-700';



type PerfilOpcao = {

  id_perfil: number;

  codigo_perfil: number;

  descricao: string;

};



function perfilPreferido(perfis: PerfilOpcao[]): PerfilOpcao | null {

  if (perfis.length === 0) return null;

  return perfis.find((p) => p.codigo_perfil === 3) ?? perfis[0];

}



/** Tela 10 Indicadores — RF-52..RF-55 (tb_indicador / tb_ind_perf). */

export function IndicadoresScreen() {

  const navigate = useNavigate();

  useScreenBg(BG);



  const [loading, setLoading] = useState(true);

  const [busy, setBusy] = useState(false);

  const [perfis, setPerfis] = useState<PerfilOpcao[]>([]);

  const [idPerfilSel, setIdPerfilSel] = useState('');

  const [indicadores, setIndicadores] = useState<IndicadorVinculoItem[]>([]);

  const [infoMsg, setInfoMsg] = useState<string | null>(null);



  const voltar = () => {

    navigate('/configuracao');

  };



  const carregarPerfis = useCallback(async () => {

    const { response, data } = await listPerfisIndicadoresConfig();

    if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

      setInfoMsg(apiErrorMessage(data, 'Falha ao carregar perfis.'));

      setPerfis([]);

      setIdPerfilSel('');

      return;

    }

    setPerfis(data.perfis);

    const preferido = perfilPreferido(data.perfis);

    setIdPerfilSel(preferido ? String(preferido.id_perfil) : '');

  }, []);



  /** RF-55 — marca checkboxes conforme tb_ind_perf do perfil selecionado. */

  const aplicarVinculosPerfil = useCallback(async (idPerfil: number) => {

    setBusy(true);

    try {

      const { response, data } = await getIndicadoresVinculoPerfil(idPerfil);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        setInfoMsg(apiErrorMessage(data, 'Falha ao carregar vínculos do perfil.'));

        return;

      }

      setIndicadores(data.indicadores);

    } catch {

      setInfoMsg('Não foi possível conectar à API.');

    } finally {

      setBusy(false);

    }

  }, []);



  useEffect(() => {

    let cancelled = false;

    (async () => {

      try {

        const { response, data } = await me();

        if (!response.ok || !data || !('usuario' in data)) {

          navigate('/', { replace: true });

          return;

        }

        if (!canAccessConfiguracao(data.usuario.codigo_perfil)) {

          navigate('/principal', { replace: true });

          return;

        }

        if (!cancelled) {

          await carregarPerfis();

        }

      } catch {

        navigate('/', { replace: true });

      } finally {

        if (!cancelled) setLoading(false);

      }

    })();

    return () => {

      cancelled = true;

    };

  }, [carregarPerfis, navigate]);



  useEffect(() => {

    const id = Number(idPerfilSel);

    if (!Number.isFinite(id) || id <= 0) return;

    void aplicarVinculosPerfil(id);

  }, [idPerfilSel, aplicarVinculosPerfil]);



  const toggleIndicador = (idInd: number) => {

    if (busy) return;

    setIndicadores((prev) =>

      prev.map((ind) =>

        ind.id_ind === idInd ? { ...ind, vinculado: !ind.vinculado } : ind,

      ),

    );

  };



  /** RF-53 — persiste checkboxes selecionados em tb_ind_perf. */

  const confirmar = async () => {

    const idPerfil = Number(idPerfilSel);

    if (!Number.isFinite(idPerfil) || idPerfil <= 0) {

      setInfoMsg('Selecione um perfil.');

      return;

    }

    if (busy) return;



    setBusy(true);

    try {

      const idInds = indicadores.filter((i) => i.vinculado).map((i) => i.id_ind);

      const { response, data } = await saveIndicadoresVinculoPerfil(

        idPerfil,

        idInds,

      );

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        setInfoMsg(apiErrorMessage(data, 'Falha ao salvar vínculos.'));

        return;

      }

      setInfoMsg(data.mensagem);

      await aplicarVinculosPerfil(idPerfil);

    } catch {

      setInfoMsg('Não foi possível conectar à API.');

    } finally {

      setBusy(false);

    }

  };



  return (

    <div className="flex min-h-[100dvh] flex-col" style={{ backgroundColor: BG }}>

      <PageHeader title="INDICADORES" onBack={voltar} />



      <div className="flex min-h-0 flex-1 flex-col px-4 pb-4 pt-3">

        <div className="flex w-full max-w-[50%] flex-col gap-1.5">

          <Label className={labelClass}>Perfil:</Label>

          <Select

            value={idPerfilSel || undefined}

            onValueChange={setIdPerfilSel}

            disabled={loading || perfis.length === 0 || busy}

          >

            <SelectTrigger className={selectTriggerClass}>

              <SelectValue placeholder="Selecione" />

            </SelectTrigger>

            <SelectContent>

              {perfis.map((p) => (

                <SelectItem key={p.id_perfil} value={String(p.id_perfil)}>

                  {p.descricao}

                </SelectItem>

              ))}

            </SelectContent>

          </Select>

        </div>



        <div className="mt-3 w-1/2 border-t-2 border-slate-500/50" />



        <div className="mt-3 min-h-0 flex-1 overflow-y-auto rounded-lg border border-slate-400/50 bg-white/70">

          {loading ? (

            <p className="p-4 text-sm text-slate-700">Carregando…</p>

          ) : indicadores.length === 0 ? (

            <p className="p-4 text-sm text-slate-700">

              Nenhum indicador cadastrado em tb_indicador.

            </p>

          ) : (

            <Table>

              <TableHeader>

                <TableRow className="bg-[#A8B9C9] hover:bg-[#A8B9C9]">

                  <TableHead className={`w-12 text-center text-[12px] ${tableHeadClass}`}>

                    {' '}

                  </TableHead>

                  <TableHead

                    className={`w-[28%] pl-1 text-left text-[13px] ${tableHeadClass}`}

                  >

                    Indicador

                  </TableHead>

                  <TableHead className={`text-left text-[13px] ${tableHeadClass}`}>

                    Descrição

                  </TableHead>

                </TableRow>

              </TableHeader>

              <TableBody>

                {indicadores.map((ind, i) => (

                  <TableRow

                    key={ind.id_ind}

                    className={i % 2 === 0 ? 'bg-white' : 'bg-[#E8EEF4]'}

                  >

                    <TableCell className="text-center">

                      <input

                        type="checkbox"

                        checked={ind.vinculado}

                        disabled={busy || !idPerfilSel}

                        onChange={() => toggleIndicador(ind.id_ind)}

                        aria-label={`Vincular indicador ${ind.descricao}`}

                        className="h-4 w-4 accent-primary"

                      />

                    </TableCell>

                    <TableCell className={`whitespace-nowrap pl-1 ${tableSiglaClass}`}>

                      {ind.descricao}

                    </TableCell>

                    <TableCell className={tableDetalheClass}>

                      {ind.detalhe?.trim() || ind.descricao}

                    </TableCell>

                  </TableRow>

                ))}

              </TableBody>

            </Table>

          )}

        </div>



        <div className="mt-auto pt-4">

          <Separator className="bg-black" />

          <div className="grid grid-cols-2 gap-3 pt-3">

            <Button

              type="button"

              className={actionBtn3dMd}

              disabled={busy || loading || !idPerfilSel}

              onClick={() => void confirmar()}

            >

              Confirmar

            </Button>

            <Button

              type="button"

              className={actionBtn3dMd}

              disabled={busy}

              onClick={voltar}

            >

              Cancelar

            </Button>

          </div>

        </div>

      </div>



      <AppDialog

        open={infoMsg !== null}

        message={infoMsg ?? ''}

        confirmLabel="OK"

        onConfirm={() => setInfoMsg(null)}

      />

    </div>

  );

}


