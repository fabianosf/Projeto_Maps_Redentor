import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { getBancoHorasMotorista, type BancoHorasDia } from '@/api/bancoHoras';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
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
import type { MotoristaCadastro } from '@/types/cadastro';
import { canAccessBancoHoras } from '@/utils/perfilAccess';
import { SCREEN_BG } from '@/theme/tokens';

const BG = SCREEN_BG;

function hojeISO(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatHoraCurta(iso: string | null | undefined): string {
  if (!iso) return '—';
  const t = String(iso).replace('T', ' ');
  const m = t.match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : t;
}

/** Controle operacional de horas do motorista (não é folha/RH). */
export function BancoHorasScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(BG);

  const [motoristas, setMotoristas] = useState<MotoristaCadastro[]>([]);
  const [idMotorista, setIdMotorista] = useState('');
  const [data, setData] = useState(hojeISO());
  const [loading, setLoading] = useState(true);
  const [consultando, setConsultando] = useState(false);
  const [banco, setBanco] = useState<BancoHorasDia | null>(null);

  const podeAcessar = canAccessBancoHoras(user?.codigo_perfil);

  useEffect(() => {
    if (!podeAcessar) {
      navigate('/principal', { replace: true });
      return;
    }
    void (async () => {
      try {
        const res = await getCadastros();
        setMotoristas(
          (res.cadastros?.motoristas ?? []).filter(
            (m) => m.ativo == null || Number(m.ativo) === 1,
          ),
        );
      } catch (err) {
        toast.error(
          err instanceof ApiRequestError
            ? err.message
            : 'Falha ao carregar motoristas.',
        );
      } finally {
        setLoading(false);
      }
    })();
  }, [navigate, podeAcessar]);

  const motoristaLabel = useMemo(() => {
    const m = motoristas.find((x) => String(x.id_motorista) === idMotorista);
    if (!m) return '';
    return `${m.matricula} — ${m.nome}`;
  }, [idMotorista, motoristas]);

  const consultar = useCallback(async () => {
    if (!idMotorista || !data) {
      toast.error('Selecione o motorista e a data.');
      return;
    }
    setConsultando(true);
    try {
      const res = await getBancoHorasMotorista(Number(idMotorista), data);
      setBanco(res.banco_horas);
    } catch (err) {
      setBanco(null);
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha na consulta.',
      );
    } finally {
      setConsultando(false);
    }
  }, [data, idMotorista]);

  if (!podeAcessar) return null;

  if (loading) {
    return (
      <AppShell className="bg-screen">
        <div className="page min-h-dvh bg-screen text-slate-900">
          <PageHeader title="Banco de horas" onBack={() => navigate('/registros')} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="Banco de horas" onBack={() => navigate('/registros')} />
        <div className="page-body flex min-h-0 flex-1 flex-col gap-4">
          <p className="text-sm text-slate-700">
            Controle operacional — não é integração oficial de folha de pagamento.
          </p>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="flex flex-col gap-1">
              <Label className="text-[13px] font-semibold uppercase">Motorista</Label>
              <Select value={idMotorista} onValueChange={(v) => setIdMotorista(v ?? '')}>
                <SelectTrigger className="h-10 bg-white">
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {motoristas.map((m) => (
                    <SelectItem key={m.id_motorista} value={String(m.id_motorista)}>
                      {m.matricula} — {m.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <FormField
              label="Data"
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              className="h-10"
            />
            <div className="flex items-end">
              <Button
                type="button"
                className="h-10 w-full"
                disabled={consultando}
                onClick={() => void consultar()}
              >
                Consultar
              </Button>
            </div>
          </div>

          {!banco ? (
            <EmptyState
              title="Consulta operacional"
              description="Selecione motorista e data para consultar o controle operacional."
            />
          ) : (
            <section className="space-y-3 rounded-xl border border-slate-400/40 bg-white/50 p-4">
              <div>
                <p className="text-base font-bold text-primary">
                  {banco.motorista.matricula} — {banco.motorista.nome}
                </p>
                <p className="text-sm text-muted-foreground">
                  {banco.data}
                  {motoristaLabel ? ` · ${motoristaLabel}` : ''}
                </p>
                <p className="mt-1 text-lg font-bold">
                  Total do dia: {banco.total_encerrado_hhmm} (
                  {banco.total_minutos_encerrados} min)
                </p>
                {banco.escala_em_andamento ? (
                  <p className="text-sm text-amber-800">
                    Estimativa em andamento:{' '}
                    {banco.total_estimativa_andamento_hhmm} (não somada ao total
                    encerrado)
                  </p>
                ) : null}
              </div>

              {banco.alertas?.length ? (
                <ul className="list-disc space-y-1 pl-5 text-sm text-amber-900">
                  {banco.alertas.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              ) : null}

              <div className="overflow-hidden rounded-xl border border-slate-400/40">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                      <TableHead className="text-[11px]">Veículo</TableHead>
                      <TableHead className="text-[11px]">Início</TableHead>
                      <TableHead className="text-[11px]">Fim</TableHead>
                      <TableHead className="text-[11px]">Duração</TableHead>
                      <TableHead className="text-[11px]">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {banco.escalas_encerradas.length === 0 &&
                    !banco.escala_em_andamento ? (
                      <TableRow>
                        <TableCell colSpan={5} className="py-6 text-muted-foreground">
                          Nenhuma escala neste dia.
                        </TableCell>
                      </TableRow>
                    ) : (
                      <>
                        {banco.escalas_encerradas.map((e) => (
                          <TableRow key={e.id_item}>
                            <TableCell className="text-xs font-medium">
                              {e.numero_frota}
                            </TableCell>
                            <TableCell className="text-xs">
                              {formatHoraCurta(e.inicio_real)}
                            </TableCell>
                            <TableCell className="text-xs">
                              {formatHoraCurta(e.fim_real)}
                            </TableCell>
                            <TableCell className="text-xs">
                              {e.duracao_trabalhada_hhmm}
                            </TableCell>
                            <TableCell className="text-xs">Encerrada</TableCell>
                          </TableRow>
                        ))}
                        {banco.escala_em_andamento ? (
                          <TableRow>
                            <TableCell className="text-xs font-medium">
                              {banco.escala_em_andamento.numero_frota}
                            </TableCell>
                            <TableCell className="text-xs">
                              {formatHoraCurta(banco.escala_em_andamento.inicio_real)}
                            </TableCell>
                            <TableCell className="text-xs">—</TableCell>
                            <TableCell className="text-xs">
                              {banco.escala_em_andamento.duracao_estimada_hhmm}{' '}
                              <span className="text-amber-800">(Estimativa)</span>
                            </TableCell>
                            <TableCell className="text-xs">Em andamento</TableCell>
                          </TableRow>
                        ) : null}
                      </>
                    )}
                  </TableBody>
                </Table>
              </div>
            </section>
          )}
        </div>
      </div>
    </AppShell>
  );
}
