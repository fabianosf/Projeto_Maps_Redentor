import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  getBancoHorasPeriodo,
  type BancoHorasDia,
  type BancoHorasEscalaAndamento,
  type BancoHorasEscalaEncerrada,
} from '@/api/bancoHoras';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import { AppShell } from '@/components/AppShell';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import type { MotoristaCadastro } from '@/types/cadastro';
import { canAccessBancoHoras } from '@/utils/perfilAccess';
import { AUTH_BG } from '@/theme/tokens';

function hojeISO(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function diasAtrasISO(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
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

function labelSituacao(s?: string | null): string {
  switch ((s || '').toLowerCase()) {
    case 'encerrada':
      return 'Encerrada';
    case 'em_andamento':
      return 'Em andamento';
    case 'mista':
      return 'Mista';
    default:
      return 'Sem registro';
  }
}

type EscalaDetalhe = BancoHorasEscalaEncerrada | BancoHorasEscalaAndamento;

/** Controle operacional de horas do motorista (não é folha/RH). */
export function BancoHorasScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(AUTH_BG);

  const [motoristas, setMotoristas] = useState<MotoristaCadastro[]>([]);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [idMotorista, setIdMotorista] = useState('');
  const [dataIni, setDataIni] = useState(diasAtrasISO(7));
  const [dataFim, setDataFim] = useState(hojeISO());
  const [idEmpresa, setIdEmpresa] = useState('');
  const [idLinha, setIdLinha] = useState('');
  const [situacao, setSituacao] = useState('');
  const [loading, setLoading] = useState(true);
  const [consultando, setConsultando] = useState(false);
  const [dias, setDias] = useState<BancoHorasDia[]>([]);
  const [detalheDia, setDetalheDia] = useState<BancoHorasDia | null>(null);
  const [detalheEscala, setDetalheEscala] = useState<EscalaDetalhe | null>(null);

  const podeAcessar = canAccessBancoHoras(user?.codigo_perfil);

  useEffect(() => {
    if (!podeAcessar) {
      navigate('/principal', { replace: true });
      return;
    }
    void (async () => {
      try {
        const res = await getCadastros();
        setCadastros(res.cadastros);
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

  const linhasFiltradas = useMemo(() => {
    const linhas = cadastros?.linhas ?? [];
    if (!idEmpresa) return linhas;
    return linhas.filter((l) => String(l.id_empresa) === idEmpresa);
  }, [cadastros?.linhas, idEmpresa]);

  const consultar = useCallback(async () => {
    if (!idMotorista || !dataIni || !dataFim) {
      toast.error('Selecione o motorista e o período.');
      return;
    }
    setConsultando(true);
    try {
      const res = await getBancoHorasPeriodo(
        Number(idMotorista),
        dataIni,
        dataFim,
        {
          id_empresa: idEmpresa ? Number(idEmpresa) : null,
          id_linha: idLinha ? Number(idLinha) : null,
          situacao: situacao || null,
        },
      );
      setDias(res.banco_horas_periodo.dias);
      if (!res.banco_horas_periodo.dias.length) {
        toast.message('Nenhum dia com movimento no período.');
      }
    } catch (err) {
      setDias([]);
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha na consulta.',
      );
    } finally {
      setConsultando(false);
    }
  }, [dataFim, dataIni, idEmpresa, idLinha, idMotorista, situacao]);

  if (!podeAcessar) return null;

  if (loading) {
    return (
      <AppShell className="bg-background">
        <div className="page min-h-dvh bg-background text-foreground">
          <PageHeader title="Banco de horas" />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-background">
      <div className="page flex min-h-dvh flex-col bg-background text-foreground">
        <PageHeader title="Banco de horas" />
        <div className="page-body flex min-h-0 flex-1 flex-col gap-4 pb-tabbar">
          <p className="text-sm text-muted-foreground">
            Histórico diário operacional — chegadas nunca são geradas pelo fim
            previsto da escala.
          </p>

          <div className="surface-card space-y-3 rounded-2xl p-4">
            <div className="flex flex-col gap-1">
              <Label className="text-[13px] font-semibold">Motorista</Label>
              <Select value={idMotorista} onValueChange={(v) => setIdMotorista(v ?? '')}>
                <SelectTrigger className="h-11 bg-card">
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

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="De"
                type="date"
                value={dataIni}
                onChange={(e) => setDataIni(e.target.value)}
              />
              <FormField
                label="Até"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <Label className="text-[13px] font-semibold">Empresa</Label>
                <Select
                  value={idEmpresa || '__all__'}
                  onValueChange={(v) => {
                    const next = v === '__all__' ? '' : (v ?? '');
                    setIdEmpresa(next);
                    setIdLinha('');
                  }}
                >
                  <SelectTrigger className="h-11 bg-card">
                    <SelectValue placeholder="Todas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">Todas</SelectItem>
                    {(cadastros?.empresas ?? []).map((e) => (
                      <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>
                        {e.descricao}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1">
                <Label className="text-[13px] font-semibold">Linha</Label>
                <Select
                  value={idLinha || '__all__'}
                  onValueChange={(v) => setIdLinha(v === '__all__' ? '' : (v ?? ''))}
                >
                  <SelectTrigger className="h-11 bg-card">
                    <SelectValue placeholder="Todas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">Todas</SelectItem>
                    {linhasFiltradas.map((l) => (
                      <SelectItem key={l.id_linha} value={String(l.id_linha)}>
                        {l.codigo_linha}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <Label className="text-[13px] font-semibold">Situação</Label>
              <Select
                value={situacao || '__all__'}
                onValueChange={(v) => setSituacao(v === '__all__' ? '' : (v ?? ''))}
              >
                <SelectTrigger className="h-11 bg-card">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">Todas</SelectItem>
                  <SelectItem value="encerrada">Encerrada</SelectItem>
                  <SelectItem value="em_andamento">Em andamento</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              type="button"
              className="ds-cta w-full"
              disabled={consultando}
              onClick={() => void consultar()}
            >
              {consultando ? 'Consultando…' : 'Consultar período'}
            </Button>
          </div>

          {!dias.length ? (
            <EmptyState
              title="Histórico diário"
              description="Selecione motorista, período e filtros para ver a jornada dia a dia."
            />
          ) : (
            <ul className="flex flex-col gap-3">
              {dias.map((dia) => (
                <li key={dia.data}>
                  <button
                    type="button"
                    className="surface-card w-full rounded-2xl px-4 py-3.5 text-left transition-colors hover:bg-card/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    onClick={() => {
                      setDetalheDia(dia);
                      setDetalheEscala(null);
                    }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-bold text-primary">{dia.data}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {labelSituacao(dia.situacao)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold tabular-nums">
                          {dia.total_encerrado_hhmm}
                        </p>
                        {dia.saldo_diario_hhmm ? (
                          <p className="text-xs text-muted-foreground">
                            Saldo {dia.saldo_diario_hhmm}
                          </p>
                        ) : null}
                      </div>
                    </div>
                    <p className="mt-2 text-[12px] text-slate-600">
                      Previsto / eventos reais por escala — toque para detalhar.
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <Dialog
          open={detalheDia != null}
          onOpenChange={(open) => {
            if (!open) {
              setDetalheDia(null);
              setDetalheEscala(null);
            }
          }}
        >
          <DialogContent className="max-w-[400px] gap-0 p-0">
            <DialogHeader className="border-b border-border/60 px-5 py-4 text-left">
              <DialogTitle>Jornada do dia</DialogTitle>
              <DialogDescription>
                {detalheDia?.data} · {detalheDia?.motorista.matricula} —{' '}
                {detalheDia?.motorista.nome}
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[65dvh] space-y-3 overflow-y-auto px-5 py-4">
              {detalheDia ? (
                <>
                  <p className="text-sm">
                    Total trabalhado:{' '}
                    <strong>{detalheDia.total_encerrado_hhmm}</strong>
                    {detalheDia.saldo_diario_hhmm
                      ? ` · Saldo ${detalheDia.saldo_diario_hhmm}`
                      : ''}
                  </p>
                  {[
                    ...detalheDia.escalas_encerradas,
                    ...(detalheDia.escala_em_andamento
                      ? [detalheDia.escala_em_andamento]
                      : []),
                  ].map((esc) => (
                    <button
                      key={esc.id_item}
                      type="button"
                      className="w-full rounded-xl border border-border/70 bg-card px-3 py-2.5 text-left"
                      onClick={() => setDetalheEscala(esc)}
                    >
                      <p className="text-sm font-bold">
                        Carro {esc.numero_frota} · {labelSituacao(esc.situacao)}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Previsto {formatHoraCurta(esc.jornada_prevista_ini)} →{' '}
                        {formatHoraCurta(esc.jornada_prevista_fim)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Real {formatHoraCurta(esc.inicio_real)} →{' '}
                        {esc.fim_real
                          ? formatHoraCurta(esc.fim_real)
                          : 'em aberto (sem chegada automática)'}
                      </p>
                      {esc.responsavel_registro ? (
                        <p className="mt-1 text-[11px] text-slate-600">
                          Responsável: {esc.matricula_responsavel} —{' '}
                          {esc.responsavel_registro}
                        </p>
                      ) : null}
                    </button>
                  ))}
                </>
              ) : null}

              {detalheEscala ? (
                <div className="rounded-xl border border-primary/20 bg-secondary/40 p-3">
                  <p className="text-sm font-bold text-primary">Viagens da escala</p>
                  {(detalheEscala.viagens?.length ?? 0) === 0 ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Nenhuma viagem cadastrada nesta escala.
                    </p>
                  ) : (
                    <ul className="mt-2 space-y-1.5">
                      {detalheEscala.viagens!.map((v) => (
                        <li
                          key={v.id_viagem}
                          className="rounded-lg border border-border/50 bg-card px-2 py-1.5 text-xs"
                        >
                          Saída {v.horario_saida ?? '—'} → Chegada{' '}
                          {v.horario_chegada ?? '—'}
                          {v.qtd_pas_ida != null || v.qtd_pas_volta != null
                            ? ` · IDA ${v.qtd_pas_ida ?? '—'} / VOLTA ${v.qtd_pas_volta ?? '—'}`
                            : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : null}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
