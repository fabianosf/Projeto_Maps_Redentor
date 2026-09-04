import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiRequestError } from '@/api/client';
import { getIndicadoresPermitidosMe } from '@/api/indicadoresConfig';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
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
import type { IndicadorPermitido } from '@/types/indicador';

const BG = '#B9C8D4';

const tableHeadClass = 'font-sans font-normal uppercase tracking-wide text-slate-700';
const tableSiglaClass = 'font-sans text-[13px] font-bold text-slate-900';
const tableDetalheClass = 'font-sans text-[13px] font-normal text-slate-700';

/**
 * Tela operacional de Indicadores — somente os autorizados ao perfil logado (RN-08).
 * Não confundir com IndicadoresConfigScreen (Tela 10 / Configuração).
 */
export function IndicadoresScreen() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  useScreenBg(BG);

  const [loading, setLoading] = useState(true);
  const [indicadores, setIndicadores] = useState<IndicadorPermitido[]>([]);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIndicadoresPermitidosMe();
      setIndicadores(data.indicadores);
    } catch (e) {
      setIndicadores([]);
      setError(
        e instanceof ApiRequestError
          ? e.message
          : 'Não foi possível carregar os indicadores.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }
    void carregar();
  }, [authLoading, user, carregar, navigate]);

  return (
    <AppShell className="flex min-h-[100dvh] flex-col bg-[#B9C8D4]">
      <PageHeader title="INDICADORES" onBack={() => navigate('/principal')} />

      <div className="flex min-h-0 flex-1 flex-col px-4 pb-4 pt-3">
        <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-slate-400/50 bg-white/70">
          {loading || authLoading ? (
            <LoadingState label="Carregando indicadores…" />
          ) : error ? (
            <ErrorState message={error} onRetry={() => void carregar()} />
          ) : indicadores.length === 0 ? (
            <EmptyState
              title="Nenhum indicador autorizado"
              description="Seu perfil não possui indicadores vinculados."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#A8B9C9] hover:bg-[#A8B9C9]">
                  <TableHead className={`w-[28%] pl-2 text-left text-[13px] ${tableHeadClass}`}>
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
                    <TableCell className={`whitespace-nowrap pl-2 ${tableSiglaClass}`}>
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
      </div>
    </AppShell>
  );
}
