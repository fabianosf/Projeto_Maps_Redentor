import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiRequestError } from '@/api/client';
import {
  getIndicadoresPorPerfil,
  getPerfisIndicadores,
  saveIndicadoresPerfil,
} from '@/api/indicadoresConfig';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
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
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import type { IndicadorVinculo } from '@/types/indicador';
import { canAccessConfiguracao } from '@/utils/perfilAccess';
import { SCREEN_BG } from '@/theme/tokens';

const BG = SCREEN_BG;

const labelClass =
  'flex h-5 items-center font-sans text-[12px] font-normal uppercase leading-none tracking-wide text-text-muted';

const selectTriggerClass =
  'h-10 w-full rounded-lg border-slate-400 bg-white font-sans text-[15px] font-normal text-text';

const tableHeadClass = 'font-sans font-normal uppercase tracking-wide text-text';
const tableSiglaClass = 'font-sans text-[13px] font-bold text-text';
const tableDetalheClass = 'font-sans text-[13px] font-normal text-text';

type PerfilOpcao = {
  id_perfil: number;
  codigo_perfil: number;
  descricao: string;
};

function perfilPreferido(perfis: PerfilOpcao[]): PerfilOpcao | null {
  if (perfis.length === 0) return null;
  return perfis.find((p) => p.codigo_perfil === 3) ?? perfis[0];
}

/** Tela 10 — vínculo perfil × indicador (RF-52..RF-55). Admin/Inspetor. */
export function IndicadoresConfigScreen() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  useScreenBg(BG);

  const allowed = canAccessConfiguracao(user?.codigo_perfil);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [perfis, setPerfis] = useState<PerfilOpcao[]>([]);
  const [idPerfilSel, setIdPerfilSel] = useState('');
  const [indicadores, setIndicadores] = useState<IndicadorVinculo[]>([]);
  /** Snapshot do servidor — Cancelar descarta alterações locais. */
  const snapshotRef = useRef<IndicadorVinculo[]>([]);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const voltar = () => navigate('/mais');

  const carregarVinculos = useCallback(async (idPerfil: number) => {
    setBusy(true);
    try {
      const data = await getIndicadoresPorPerfil(idPerfil);
      setIndicadores(data.indicadores);
      snapshotRef.current = data.indicadores.map((i) => ({ ...i }));
    } catch (e) {
      setInfoMsg(
        e instanceof ApiRequestError
          ? e.message
          : 'Falha ao carregar vínculos do perfil.',
      );
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }
    if (!allowed) {
      navigate('/principal', { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await getPerfisIndicadores();
        if (cancelled) return;
        setPerfis(data.perfis);
        const preferido = perfilPreferido(data.perfis);
        setIdPerfilSel(preferido ? String(preferido.id_perfil) : '');
      } catch (e) {
        if (!cancelled) {
          setInfoMsg(
            e instanceof ApiRequestError ? e.message : 'Falha ao carregar perfis.',
          );
          setPerfis([]);
          setIdPerfilSel('');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [authLoading, user, allowed, navigate]);

  /** RF-55 — trocar perfil recarrega e marca os já associados. */
  useEffect(() => {
    const id = Number(idPerfilSel);
    if (!Number.isFinite(id) || id <= 0) return;
    void carregarVinculos(id);
  }, [idPerfilSel, carregarVinculos]);

  const toggleIndicador = (idInd: number) => {
    if (busy) return;
    setIndicadores((prev) =>
      prev.map((ind) =>
        ind.id_ind === idInd ? { ...ind, vinculado: !ind.vinculado } : ind,
      ),
    );
  };

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
      const data = await saveIndicadoresPerfil(idPerfil, idInds);
      setInfoMsg(data.mensagem);
      await carregarVinculos(idPerfil);
    } catch (e) {
      setInfoMsg(
        e instanceof ApiRequestError ? e.message : 'Não foi possível conectar à API.',
      );
    } finally {
      setBusy(false);
    }
  };

  /** Cancelar — não persiste; restaura snapshot e volta. */
  const cancelar = () => {
    setIndicadores(snapshotRef.current.map((i) => ({ ...i })));
    voltar();
  };

  if (authLoading || (allowed && loading && perfis.length === 0 && !infoMsg)) {
    return (
      <AppShell className="bg-screen">
        <PageHeader title="INDICADORES" />
        <LoadingState label="Carregando…" />
      </AppShell>
    );
  }

  if (!allowed) return null;

  return (
    <AppShell className="flex min-h-[100dvh] flex-col bg-screen">
      <PageHeader title="INDICADORES" />

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

        <div className="mt-3 min-h-0 flex-1 overflow-y-auto rounded-lg border border-field bg-surface-card">
          {busy && indicadores.length === 0 ? (
            <LoadingState label="Carregando indicadores…" />
          ) : indicadores.length === 0 ? (
            <EmptyState title="Nenhum indicador cadastrado" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-table-head hover:bg-table-head">
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
                    className={i % 2 === 0 ? 'bg-white' : 'bg-table-zebra'}
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
              onClick={cancelar}
            >
              Cancelar
            </Button>
          </div>
        </div>
      </div>

      <AlertDialog
        open={infoMsg !== null}
        message={infoMsg ?? ''}
        confirmLabel="OK"
        onConfirm={() => setInfoMsg(null)}
      />
    </AppShell>
  );
}
