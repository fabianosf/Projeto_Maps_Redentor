import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Map, Settings, UsersRound } from 'lucide-react';
import { toast } from 'sonner';
import { me } from '@/api/auth';
import { getCadastros, getIndicadores } from '@/api/mapa';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { UsuarioPublico } from '@/types';
import type { LinhaCadastro } from '@/types/mapa';
import { apiErrorMessage } from '@/utils/mapaFormat';

const BG = '#B9C8D4';

function formatCodigoLinha(linha: LinhaCadastro): string {
  const raw = linha.codigo_linha;
  if (raw != null && Number.isFinite(Number(raw))) {
    return String(Math.trunc(Number(raw)));
  }
  return String(linha.descricao ?? linha.id_linha);
}

/** Tela_Principal — pós-login (MAPA / CONFIGURAÇÃO + Indicadores). */
export function TelaPrincipalScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);

  const [usuario, setUsuario] = useState<UsuarioPublico | null>(null);
  const [linhas, setLinhas] = useState<LinhaCadastro[]>([]);
  const [qtcM, setQtcM] = useState<number | null>(null);
  const [codigoLinhaSel, setCodigoLinhaSel] = useState<string | null>(null);
  const [idLinhaSel, setIdLinhaSel] = useState<number | null>(null);
  const [loadingInd, setLoadingInd] = useState(false);

  const [modalOpen, setModalOpen] = useState(false);
  const [linhaDraft, setLinhaDraft] = useState<string>('');
  const [busyModal, setBusyModal] = useState(false);

  const carregarSessao = useCallback(async () => {
    try {
      const [meRes, cadRes] = await Promise.all([me(), getCadastros()]);
      if (meRes.response.ok && meRes.data && 'usuario' in meRes.data) {
        setUsuario(meRes.data.usuario);
      } else {
        setUsuario(null);
        navigate('/', { replace: true });
        return;
      }
      if (
        cadRes.response.ok &&
        cadRes.data &&
        'ok' in cadRes.data &&
        cadRes.data.ok === true
      ) {
        setLinhas(cadRes.data.cadastros.linhas ?? []);
      } else {
        setLinhas([]);
      }
    } catch {
      setLinhas([]);
    }
  }, [navigate]);

  useEffect(() => {
    void carregarSessao();
  }, [carregarSessao]);

  const aplicarIndicador = useCallback(async (idLinha: number) => {
    setLoadingInd(true);
    setBusyModal(true);
    try {
      const { response, data } = await getIndicadores(idLinha);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        toast.error(apiErrorMessage(data, 'Falha ao calcular Qtc/M.'));
        return false;
      }
      const ind = data.indicadores;
      setQtcM(typeof ind.qtc_m === 'number' ? ind.qtc_m : null);
      setIdLinhaSel(ind.id_linha ?? idLinha);
      if (ind.codigo_linha != null && ind.codigo_linha !== '') {
        setCodigoLinhaSel(String(ind.codigo_linha));
      } else {
        setCodigoLinhaSel(String(idLinha));
      }
      return true;
    } catch {
      toast.error('Não foi possível conectar à API.');
      return false;
    } finally {
      setLoadingInd(false);
      setBusyModal(false);
    }
  }, []);

  const abrirModal = () => {
    setLinhaDraft(idLinhaSel != null ? String(idLinhaSel) : '');
    setModalOpen(true);
  };

  const confirmarLinha = async (idLinhaStr: string) => {
    const id = Number(idLinhaStr);
    if (!Number.isFinite(id) || id <= 0) {
      toast.message('Selecione uma linha.');
      return;
    }
    const ok = await aplicarIndicador(id);
    if (ok) setModalOpen(false);
  };

  const opcoesLinha = useMemo(
    () =>
      [...linhas].sort((a, b) => {
        const ca = Number(a.codigo_linha);
        const cb = Number(b.codigo_linha);
        if (Number.isFinite(ca) && Number.isFinite(cb)) return ca - cb;
        return formatCodigoLinha(a).localeCompare(formatCodigoLinha(b));
      }),
    [linhas],
  );

  const labelQtc = codigoLinhaSel ? `QTC/M(${codigoLinhaSel})` : 'QTC/M';
  const podeConfigurar = usuario?.codigo_perfil === 1;

  return (
    <div className="page h-dvh max-h-dvh overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader title="RedMapa" />

      <div className="flex min-h-0 flex-1 flex-col bg-[#B9C8D4]">
        <div className="flex shrink-0 flex-col items-center justify-center gap-4 px-6 py-8">
          <Button
            type="button"
            className="h-14 w-full max-w-[280px] gap-2 text-[15px]"
            onClick={() => navigate('/lista-mapa')}
          >
            <Map className="h-5 w-5" strokeWidth={2.25} />
            MAPA
          </Button>
          <Button
            type="button"
            className="h-14 w-full max-w-[280px] gap-2 text-[15px]"
            disabled={!podeConfigurar}
            onClick={() => navigate('/configuracao')}
          >
            <Settings className="h-5 w-5" strokeWidth={2.25} />
            CONFIGURAÇÃO
          </Button>
        </div>

        <div className="mx-5 shrink-0 border-t-2 border-slate-500/50" />

        <div className="min-h-0 flex-1 px-5 py-5">
          <h2 className="mb-4 text-center text-[18px] font-bold uppercase tracking-wide text-slate-900">
            Indicadores
          </h2>

          <div className="flex items-start justify-start">
            <div className="flex min-w-[88px] flex-col items-center gap-1">
              <span className="text-[12px] font-bold uppercase tracking-wide text-slate-800">
                {labelQtc}
              </span>
              <button
                type="button"
                onClick={abrirModal}
                className="flex h-[72px] w-[72px] flex-col items-center justify-center rounded-xl border-2 border-primary/40 bg-white/85 text-primary shadow-sm transition-colors hover:bg-white active:bg-white/70"
                title="Selecionar linha para Qtc/M"
                aria-label="Abrir seleção de linha para quantidade média de passageiros"
              >
                <UsersRound className="h-7 w-7" strokeWidth={2.25} />
                <span className="mt-1 text-[15px] font-bold tabular-nums text-slate-900">
                  {loadingInd ? '…' : qtcM == null ? '—' : qtcM}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-[340px] border-slate-400/50 bg-[#B9C8D4] p-5">
          <DialogHeader>
            <DialogTitle className="text-center text-[16px] uppercase tracking-wide text-slate-900">
              Selecionar linha
            </DialogTitle>
          </DialogHeader>

          <div className="mt-2">
            <label className="mb-1.5 block text-sm font-semibold text-slate-800">
              Linha
            </label>
            <Select
              value={linhaDraft || undefined}
              onValueChange={(v) => {
                setLinhaDraft(v);
                void confirmarLinha(v);
              }}
              disabled={busyModal || opcoesLinha.length === 0}
            >
              <SelectTrigger className="h-12 w-full rounded-lg border-slate-400 bg-white text-base text-slate-900">
                <SelectValue placeholder="Escolha a linha" />
              </SelectTrigger>
              <SelectContent position="popper" className="z-[300]">
                {opcoesLinha.map((l) => (
                  <SelectItem key={l.id_linha} value={String(l.id_linha)}>
                    {formatCodigoLinha(l)}
                    {l.descricao ? ` — ${l.descricao}` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {opcoesLinha.length === 0 ? (
              <p className="mt-2 text-center text-sm text-slate-700">
                Nenhuma linha cadastrada.
              </p>
            ) : null}
          </div>

          <DialogFooter className="mt-5">
            <Button
              type="button"
              className="w-full"
              disabled={busyModal || !linhaDraft}
              onClick={() => void confirmarLinha(linhaDraft)}
            >
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ScreenLabel text="Tela Principal" />
    </div>
  );
}
