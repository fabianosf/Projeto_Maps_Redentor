import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import {
  createItem,
  createViagem,
  deleteItem,
  deleteMapa,
  deleteViagem,
  getCadastros,
  getMapa,
} from '@/api/mapa';
import { FormField } from '@/components/forms/FormField';
import { AppAlertDialog } from '@/components/shared/AppAlertDialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { ScreenLabel } from '@/components/shared/ScreenLabel';
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
import type { CadastrosMestres, MapaCompleto } from '@/types/mapa';
import {
  apiErrorMessage,
  combineDateAndTime,
  formatCodMap,
  formatHora,
  fromDateTimeLocal,
  toDateInput,
  toDateTimeLocal,
} from '@/utils/mapaFormat';

/** Tela Mapa — carros + viagens (RF-MAP-UI-006..008) */
export function MapaScreen() {
  const navigate = useNavigate();
  const { idRegistro: idParam } = useParams();
  const idRegistro = Number(idParam);

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

  const carregar = useCallback(async () => {
    if (!Number.isFinite(idRegistro)) {
      navigate('/lista-mapa', { replace: true });
      return;
    }
    setLoading(true);
    try {
      const [mapRes, cadRes] = await Promise.all([getMapa(idRegistro), getCadastros()]);
      if (!mapRes.response.ok || !mapRes.data || !('ok' in mapRes.data) || mapRes.data.ok !== true) {
        toast.error(apiErrorMessage(mapRes.data, 'MAPA não encontrado.'));
        navigate('/lista-mapa', { replace: true });
        return;
      }
      const m = mapRes.data.mapa;
      setMapa(m);
      setSelectedItemId((prev) => {
        if (prev != null && m.itens.some((i) => i.id_item === prev)) return prev;
        return m.itens[0]?.id_item ?? null;
      });
      if (cadRes.response.ok && cadRes.data && 'ok' in cadRes.data && cadRes.data.ok === true) {
        setCadastros(cadRes.data.cadastros);
      }
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setLoading(false);
    }
  }, [idRegistro, navigate]);

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
      const { response, data } = await createItem(mapa.id_registro, {
        id_veiculo: Number(idVeiculo),
        id_motorista: Number(idMotorista),
        hor_ini_jor: fromDateTimeLocal(horIni),
        hor_fim_jor: fromDateTimeLocal(horFim),
        chegada_ponto: fromDateTimeLocal(chegada),
      });
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        toast.error(apiErrorMessage(data, 'Falha ao incluir carro.'));
        return;
      }
      toast.success('Carro incluído.');
      setItemDialog(false);
      await carregar();
      setSelectedItemId(data.item.id_item);
    } catch {
      toast.error('Falha de comunicação com a API.');
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
      const { response, data } = await createViagem(itemSelecionado.id_item, {
        horario_saida: combineDateAndTime(dataMapa, saidaHora),
        horario_chegada: combineDateAndTime(dataMapa, chegadaHora),
        qtd_pas_ida: Number(qtdIda) || 0,
        qtd_pas_volta: Number(qtdVolta) || 0,
      });
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        toast.error(apiErrorMessage(data, 'Falha ao incluir viagem.'));
        return;
      }
      toast.success('Viagem incluída.');
      setViagemDialog(false);
      await carregar();
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirMapa = async () => {
    if (!mapa) return;
    setConfirmDeleteMap(false);
    setBusy(true);
    try {
      const { response, data } = await deleteMapa(mapa.id_registro);
      if (!response.ok) {
        toast.error(apiErrorMessage(data, 'Falha ao excluir MAPA.'));
        return;
      }
      toast.success('MAPA excluído.');
      navigate('/lista-mapa', { replace: true });
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const confirmarExcluirItem = async () => {
    if (selectedItemId == null) return;
    setConfirmDeleteItem(false);
    setBusy(true);
    try {
      const { response, data } = await deleteItem(selectedItemId);
      if (!response.ok) {
        toast.error(apiErrorMessage(data, 'Falha ao excluir carro.'));
        return;
      }
      toast.success('Carro excluído.');
      setSelectedItemId(null);
      await carregar();
    } catch {
      toast.error('Falha de comunicação com a API.');
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
      const { response, data } = await deleteViagem(id);
      if (!response.ok) {
        toast.error(apiErrorMessage(data, 'Falha ao excluir viagem.'));
        return;
      }
      toast.success('Viagem excluída.');
      await carregar();
    } catch {
      toast.error('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  if (loading || !mapa) {
    return (
      <div className="page">
        <PageHeader title="MAPA" onBack={() => navigate('/lista-mapa')} />
        <p className="p-6 text-center text-sm text-muted-foreground">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="page">
      <PageHeader title="MAPA" onBack={() => navigate('/lista-mapa')} />

      <div className="page-body gap-4">
        <section className="rounded-xl border bg-card p-4">
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

          <div className="overflow-hidden rounded-xl border">
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
            <p className="text-sm text-muted-foreground">Selecione um carro para ver as viagens.</p>
          ) : (
            <div className="overflow-hidden rounded-xl border">
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

      <ScreenLabel text="Detalhe do MAPA" />

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

      <AppAlertDialog
        open={confirmDeleteMap}
        title="Excluir MAPA"
        message="Exclui o MAPA, carros e viagens. Continuar?"
        confirmLabel="Excluir"
        onConfirm={() => void confirmarExcluirMapa()}
        onCancel={() => setConfirmDeleteMap(false)}
      />

      <AppAlertDialog
        open={confirmDeleteItem}
        title="Excluir carro"
        message="Exclui o carro e suas viagens. Continuar?"
        confirmLabel="Excluir"
        onConfirm={() => void confirmarExcluirItem()}
        onCancel={() => setConfirmDeleteItem(false)}
      />

      <AppAlertDialog
        open={confirmDeleteViagem != null}
        title="Excluir viagem"
        message="Confirma a exclusão desta viagem?"
        confirmLabel="Excluir"
        onConfirm={() => void confirmarExcluirViagem()}
        onCancel={() => setConfirmDeleteViagem(null)}
      />
    </div>
  );
}
