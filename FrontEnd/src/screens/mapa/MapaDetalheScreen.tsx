import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import {
  createItem,
  createViagem,
  deleteItem,
  deleteMapa,
  deleteViagem,
  getMapa,
} from '@/api/mapa';
import { AppShell } from '@/components/AppShell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
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
import type { CadastrosMestres } from '@/types/cadastro';
import type { MapaCompleto } from '@/types/mapa';
import {
  combineDateAndTime,
  formatCodMap,
  formatHora,
  fromDateTimeLocal,
  toDateInput,
  toDateTimeLocal,
} from '@/utils/mapaFormat';

const MAPA_BG = '#B9C8D4';

/** Detalhe do MAPA — carros + viagens. Rota: `/mapas/:id` */
export function MapaDetalheScreen() {
  const navigate = useNavigate();
  const { id: idParam } = useParams();
  const idRegistro = Number(idParam);
  useScreenBg(MAPA_BG);

  const [mapa, setMapa] = useState<MapaCompleto | null>(null);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);

  const [itemDialog, setItemDialog] = useState(false);
  const [viagemDialog, setViagemDialog] = useState(false);
  const [confirmDeleteMap, setConfirmDeleteMap] = useState(false);
  const [confirmDeleteItem, setConfirmDeleteItem] = useState(false);
  const [confirmDeleteViagem, setConfirmDeleteViagem] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const [idVeiculo, setIdVeiculo] = useState('');
  const [idMotorista, setIdMotorista] = useState('');
  const [horIni, setHorIni] = useState('');
  const [horFim, setHorFim] = useState('');
  const [chegada, setChegada] = useState('');

  const [saidaHora, setSaidaHora] = useState('');
  const [chegadaHora, setChegadaHora] = useState('');
  const [qtdIda, setQtdIda] = useState('0');
  const [qtdVolta, setQtdVolta] = useState('0');

  const goLista = () => navigate('/mapas', { replace: true });

  const carregar = useCallback(async () => {
    if (!Number.isFinite(idRegistro)) {
      goLista();
      return;
    }
    setLoading(true);
    try {
      const [mapRes, cadRes] = await Promise.all([
        getMapa(idRegistro),
        getCadastros(),
      ]);
      const m = mapRes.mapa;
      setMapa(m);
      setSelectedItemId((prev) => {
        if (prev != null && m.itens.some((i) => i.id_item === prev)) return prev;
        return m.itens[0]?.id_item ?? null;
      });
      setCadastros(cadRes.cadastros);
    } catch (e) {
      const msg =
        e instanceof ApiRequestError ? e.message : 'Falha de comunicação com a API.';
      toast.error(msg);
      goLista();
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- navigate estável
  }, [idRegistro]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const itemSelecionado = useMemo(
    () => mapa?.itens.find((i) => i.id_item === selectedItemId) ?? null,
    [mapa, selectedItemId],
  );

  const openItemDialog = () => {
    if (!mapa) return;
    setIdVeiculo('');
    setIdMotorista('');
    setHorIni(toDateTimeLocal(mapa.inicio_jornada_des));
    setHorFim(toDateTimeLocal(mapa.fim_jornada_des));
    setChegada(toDateTimeLocal(mapa.inicio_jornada_des));
    setItemDialog(true);
  };

  const onSalvarItem = async (e: FormEvent) => {
    e.preventDefault();
    if (!mapa || busy) return;
    if (!idVeiculo || !idMotorista || !horIni || !horFim || !chegada) {
      toast.error('Preencha veículo, motorista e horários.');
      return;
    }
    setBusy(true);
    try {
      const data = await createItem(mapa.id_registro, {
        id_veiculo: Number(idVeiculo),
        id_motorista: Number(idMotorista),
        hor_ini_jor: fromDateTimeLocal(horIni),
        hor_fim_jor: fromDateTimeLocal(horFim),
        chegada_ponto: fromDateTimeLocal(chegada),
      });
      toast.success('Carro incluído.');
      setItemDialog(false);
      await carregar();
      setSelectedItemId(data.item.id_item);
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const onSalvarViagem = async (e: FormEvent) => {
    e.preventDefault();
    if (!mapa || !itemSelecionado || busy) return;
    if (!saidaHora || !chegadaHora) {
      toast.error('Informe saída e chegada.');
      return;
    }
    const dataMapa = toDateInput(mapa.data);
    setBusy(true);
    try {
      await createViagem(itemSelecionado.id_item, {
        horario_saida: combineDateAndTime(dataMapa, saidaHora),
        horario_chegada: combineDateAndTime(dataMapa, chegadaHora),
        qtd_pas_ida: Number(qtdIda) || 0,
        qtd_pas_volta: Number(qtdVolta) || 0,
      });
      toast.success('Viagem incluída.');
      setViagemDialog(false);
      await carregar();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirMapa = async () => {
    if (!mapa) return;
    setConfirmDeleteMap(false);
    setBusy(true);
    try {
      await deleteMapa(mapa.id_registro);
      toast.success('MAPA excluído.');
      goLista();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirItem = async () => {
    if (selectedItemId == null) return;
    setConfirmDeleteItem(false);
    setBusy(true);
    try {
      await deleteItem(selectedItemId);
      toast.success('Carro excluído.');
      setSelectedItemId(null);
      await carregar();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirViagem = async () => {
    if (confirmDeleteViagem == null) return;
    const id = confirmDeleteViagem;
    setConfirmDeleteViagem(null);
    setBusy(true);
    try {
      await deleteViagem(id);
      toast.success('Viagem excluída.');
      await carregar();
    } catch (err) {
      toast.error(
        err instanceof ApiRequestError ? err.message : 'Falha de comunicação com a API.',
      );
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

  if (!mapa) {
    return (
      <AppShell className="bg-[#B9C8D4]">
        <div className="page min-h-dvh bg-[#B9C8D4] text-slate-900">
          <PageHeader title="MAPA" onBack={goLista} />
          <EmptyState title="MAPA não encontrado" description="Volte à lista e tente novamente." />
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
              aria-label="Editar MAPA"
              onClick={() => navigate(`/mapas/${idRegistro}/editar`)}
              className="h-9 w-9 rounded border border-white/70 text-white hover:bg-white/10"
            >
              <Pencil className="h-5 w-5" strokeWidth={2.25} />
            </Button>
          }
        />

        <div className="page-body flex min-h-0 flex-1 flex-col gap-4">
          <section className="rounded-xl border border-slate-400/40 bg-white/50 p-4">
            <div className="mb-2">
              <p className="text-lg font-bold text-primary">
                Nº {formatCodMap(mapa.cod_map)}
              </p>
              <p className="text-sm text-muted-foreground">
                {toDateInput(mapa.data)} · {mapa.empresa}
              </p>
              <p className="text-sm">
                {mapa.linha} · {mapa.turno}
              </p>
              <p className="text-xs text-muted-foreground">
                Desp.: {mapa.despachante} · {formatHora(mapa.inicio_jornada_des)}–
                {formatHora(mapa.fim_jornada_des)}
              </p>
            </div>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-[13px] font-bold uppercase tracking-wide text-muted-foreground">
                Carros
              </h2>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="icon"
                  className="h-10 w-10 rounded-full"
                  aria-label="Novo carro"
                  onClick={openItemDialog}
                >
                  <Plus className="h-5 w-5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  className="h-10 w-10 rounded-full"
                  aria-label="Excluir carro"
                  disabled={selectedItemId == null}
                  onClick={() => setConfirmDeleteItem(true)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-slate-400/40">
              <Table>
                <TableHeader>
                  <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                    <TableHead className="text-[11px] leading-tight">Carro</TableHead>
                    <TableHead className="text-[11px] leading-tight">Matrícula</TableHead>
                    <TableHead className="text-[11px] leading-tight">Início</TableHead>
                    <TableHead className="text-[11px] leading-tight">Chegada</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mapa.itens.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="py-6 text-muted-foreground">
                        Nenhum carro. Toque em + para incluir.
                      </TableCell>
                    </TableRow>
                  ) : (
                    mapa.itens.map((item, i) => (
                      <TableRow
                        key={item.id_item}
                        className={`cursor-pointer ${
                          item.id_item === selectedItemId
                            ? 'bg-primary/10'
                            : i % 2 === 0
                              ? 'bg-white'
                              : 'bg-[hsl(var(--zebra))]'
                        }`}
                        onClick={() => setSelectedItemId(item.id_item)}
                      >
                        <TableCell className="text-xs">
                          {item.numero_frota ?? item.id_veiculo}
                        </TableCell>
                        <TableCell className="text-xs">
                          {item.matricula_motorista ?? '—'}
                        </TableCell>
                        <TableCell className="text-xs">{formatHora(item.hor_ini_jor)}</TableCell>
                        <TableCell className="text-xs">{formatHora(item.chegada_ponto)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>

          <Separator />

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-[13px] font-bold uppercase tracking-wide text-muted-foreground">
                Viagens {itemSelecionado ? `· ${itemSelecionado.numero_frota ?? ''}` : ''}
              </h2>
              <Button
                type="button"
                size="icon"
                className="h-10 w-10 rounded-full"
                aria-label="Nova viagem"
                disabled={!itemSelecionado}
                onClick={() => {
                  setSaidaHora('');
                  setChegadaHora('');
                  setQtdIda('0');
                  setQtdVolta('0');
                  setViagemDialog(true);
                }}
              >
                <Plus className="h-5 w-5" />
              </Button>
            </div>

            {!itemSelecionado ? (
              <p className="text-sm text-muted-foreground">
                Selecione um carro para ver as viagens.
              </p>
            ) : (
              <div className="overflow-hidden rounded-xl border border-slate-400/40">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-secondary/60 hover:bg-secondary/60">
                      <TableHead className="text-[11px]">Saída</TableHead>
                      <TableHead className="text-[11px]">Chegada</TableHead>
                      <TableHead className="text-[11px]">Qtd ida</TableHead>
                      <TableHead className="text-[11px]">Qtd volta</TableHead>
                      <TableHead className="w-10 p-0" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {itemSelecionado.viagens.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="py-6 text-muted-foreground">
                          Nenhuma viagem.
                        </TableCell>
                      </TableRow>
                    ) : (
                      itemSelecionado.viagens.map((v, i) => (
                        <TableRow
                          key={v.id_viagem}
                          className={i % 2 === 0 ? 'bg-white' : 'bg-[hsl(var(--zebra))]'}
                        >
                          <TableCell className="text-xs">{formatHora(v.horario_saida)}</TableCell>
                          <TableCell className="text-xs">{formatHora(v.horario_chegada)}</TableCell>
                          <TableCell className="text-xs">{v.qtd_pas_ida}</TableCell>
                          <TableCell className="text-xs">{v.qtd_pas_volta}</TableCell>
                          <TableCell className="p-1">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-9 w-9 text-destructive"
                              aria-label="Excluir viagem"
                              onClick={() => setConfirmDeleteViagem(v.id_viagem)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>

          <Button
            type="button"
            variant="outline"
            className="mt-auto w-full"
            disabled={busy}
            onClick={() => setConfirmDeleteMap(true)}
          >
            Excluir MAPA
          </Button>
        </div>

        <Dialog open={itemDialog} onOpenChange={setItemDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Novo carro</DialogTitle>
            </DialogHeader>
            <form className="field-stack" onSubmit={(e) => void onSalvarItem(e)}>
              <div className="flex w-full flex-col gap-1.5">
                <Label className="text-[15px] font-semibold">Veículo *</Label>
                <Select value={idVeiculo || undefined} onValueChange={setIdVeiculo}>
                  <SelectTrigger className="h-12 bg-white text-base">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {(cadastros?.veiculos ?? []).map((v) => (
                      <SelectItem key={v.id_veiculo} value={String(v.id_veiculo)}>
                        {v.numero_frota}
                        {v.placa ? ` · ${v.placa}` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex w-full flex-col gap-1.5">
                <Label className="text-[15px] font-semibold">Motorista *</Label>
                <Select value={idMotorista || undefined} onValueChange={setIdMotorista}>
                  <SelectTrigger className="h-12 bg-white text-base">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {(cadastros?.motoristas ?? []).map((m) => (
                      <SelectItem key={m.id_motorista} value={String(m.id_motorista)}>
                        {m.matricula} — {m.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <FormField
                label="Início jornada"
                requiredMark
                type="datetime-local"
                value={horIni}
                onChange={(e) => setHorIni(e.target.value)}
              />
              <FormField
                label="Fim jornada"
                requiredMark
                type="datetime-local"
                value={horFim}
                onChange={(e) => setHorFim(e.target.value)}
              />
              <FormField
                label="Chegada ao ponto"
                requiredMark
                type="datetime-local"
                value={chegada}
                onChange={(e) => setChegada(e.target.value)}
              />

              <DialogFooter className="grid grid-cols-2 gap-3">
                <Button type="submit" disabled={busy}>
                  Confirmar
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() => setItemDialog(false)}
                >
                  Cancelar
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        <Dialog open={viagemDialog} onOpenChange={setViagemDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova viagem</DialogTitle>
            </DialogHeader>
            <form className="field-stack" onSubmit={(e) => void onSalvarViagem(e)}>
              <FormField
                label="Saída"
                requiredMark
                type="time"
                value={saidaHora}
                onChange={(e) => setSaidaHora(e.target.value)}
              />
              <FormField
                label="Chegada"
                requiredMark
                type="time"
                value={chegadaHora}
                onChange={(e) => setChegadaHora(e.target.value)}
              />
              <FormField
                label="Qtd ida"
                type="number"
                min={0}
                value={qtdIda}
                onChange={(e) => setQtdIda(e.target.value)}
              />
              <FormField
                label="Qtd volta"
                type="number"
                min={0}
                value={qtdVolta}
                onChange={(e) => setQtdVolta(e.target.value)}
              />
              <DialogFooter className="grid grid-cols-2 gap-3">
                <Button type="submit" disabled={busy}>
                  Confirmar
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() => setViagemDialog(false)}
                >
                  Cancelar
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        <ConfirmDialog
          open={confirmDeleteMap}
          title="Excluir MAPA"
          message="Exclui o MAPA, carros e viagens. Continuar?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirMapa()}
          onCancel={() => setConfirmDeleteMap(false)}
        />

        <ConfirmDialog
          open={confirmDeleteItem}
          title="Excluir carro"
          message="Exclui o carro e suas viagens. Continuar?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirItem()}
          onCancel={() => setConfirmDeleteItem(false)}
        />

        <ConfirmDialog
          open={confirmDeleteViagem != null}
          title="Excluir viagem"
          message="Confirma a exclusão desta viagem?"
          confirmLabel="Excluir"
          onConfirm={() => void confirmarExcluirViagem()}
          onCancel={() => setConfirmDeleteViagem(null)}
        />
      </div>
    </AppShell>
  );
}
