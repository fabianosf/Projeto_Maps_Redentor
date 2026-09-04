import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, UserCog } from 'lucide-react';
import { ApiRequestError } from '@/api/client';
import { getQtdTentativas, saveQtdTentativas } from '@/api/config';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dBase, actionBtn3dMd } from '@/lib/actionBtn3d';
import { cn } from '@/lib/utils';
import { validarQtdMaxTentativas } from '@/utils/configValidation';
import { canAccessConfiguracao } from '@/utils/perfilAccess';
import { onlyDigits } from '@/utils/validation';

const BG = '#B9C8D4';

const toolbarBtnClass = cn(
  actionBtn3dBase,
  'flex h-[calc(39px+3mm)] w-[calc(88px+1.5cm)] shrink-0 flex-row gap-1.5 px-2 text-[11px] normal-case',
);

/** Tela 09 — Configuração (QTD tentativas + bloqueio). */
export function ConfiguracaoScreen() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  useScreenBg(BG);

  const allowed = canAccessConfiguracao(user?.codigo_perfil);

  const [loading, setLoading] = useState(true);
  const [qtdT, setQtdT] = useState('');
  const [bloqueioLogin, setBloqueioLogin] = useState(true);
  const [busy, setBusy] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getQtdTentativas();
      setQtdT(String(data.valor ?? ''));
      setBloqueioLogin(data.bloqueio_tentativas !== false);
    } catch (e) {
      setInfoMsg(
        e instanceof ApiRequestError
          ? e.message
          : 'Falha ao carregar Qtd/Tentativas de login.',
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
    if (!allowed) {
      navigate('/principal', { replace: true });
      return;
    }
    void carregar();
  }, [authLoading, user, allowed, carregar, navigate]);

  const confirmar = async () => {
    if (busy || loading || !allowed) return;

    const erroLocal = validarQtdMaxTentativas(qtdT);
    if (erroLocal) {
      setInfoMsg(erroLocal);
      return;
    }

    setBusy(true);
    try {
      const data = await saveQtdTentativas(qtdT.trim(), bloqueioLogin);
      setQtdT(String(data.valor));
      if (data.bloqueio_tentativas != null) {
        setBloqueioLogin(data.bloqueio_tentativas);
      }
      setInfoMsg(data.mensagem ?? 'Configurações de login atualizadas.');
    } catch (e) {
      setInfoMsg(
        e instanceof ApiRequestError
          ? e.message
          : 'Falha de comunicação com a API.',
      );
    } finally {
      setBusy(false);
    }
  };

  if (authLoading || (allowed && loading && !infoMsg && qtdT === '')) {
    return (
      <AppShell className="bg-[#B9C8D4]">
        <PageHeader title="CONFIGURAÇÃO" onBack={() => navigate('/principal')} />
        <LoadingState label="Carregando…" />
      </AppShell>
    );
  }

  if (!allowed) {
    return null;
  }

  return (
    <AppShell className="flex h-dvh max-h-dvh flex-col overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader title="CONFIGURAÇÃO" onBack={() => navigate('/principal')} />

      <div className="flex min-h-0 flex-1 flex-col px-4 py-8">
        <div className="mx-auto flex w-full max-w-[360px] flex-col gap-6">
          <div className="flex w-full items-start justify-center gap-[2.5cm] px-1">
            <Button
              type="button"
              className={toolbarBtnClass}
              onClick={() => navigate('/usuarios')}
              disabled={busy || loading}
            >
              <UserCog className="h-4 w-4 shrink-0" strokeWidth={2.25} />
              <span className="normal-case leading-tight text-[10px]">
                Cadastro de usuários
              </span>
            </Button>
            <Button
              type="button"
              className={toolbarBtnClass}
              onClick={() => navigate('/configuracao/indicadores')}
              disabled={busy || loading}
            >
              <BarChart3 className="h-4 w-4 shrink-0" strokeWidth={2.25} />
              <span className="normal-case leading-tight text-[10px]">Indicadores</span>
            </Button>
          </div>

          <hr className="border-0 border-t-2 border-black" />

          <div className="flex w-full flex-col gap-4 self-start px-1">
            <div className="flex items-center justify-between gap-3">
              <Label
                htmlFor="bloqueio_login"
                className="text-[12px] font-normal leading-snug text-slate-900"
              >
                Login (Bloqueio de tentativas de acesso):
              </Label>
              <button
                id="bloqueio_login"
                type="button"
                role="switch"
                aria-checked={bloqueioLogin}
                aria-label={
                  bloqueioLogin
                    ? 'Bloqueio de tentativas ativo'
                    : 'Bloqueio de tentativas inativo'
                }
                disabled={loading || busy}
                onClick={() => setBloqueioLogin((v) => !v)}
                className={cn(
                  'relative h-7 w-12 shrink-0 rounded-full transition-colors',
                  bloqueioLogin ? 'bg-[#1e3a5f]' : 'bg-slate-400',
                  (loading || busy) && 'opacity-60',
                )}
              >
                <span
                  className={cn(
                    'absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform',
                    bloqueioLogin ? 'left-5' : 'left-0.5',
                  )}
                />
              </button>
            </div>

            <div className="flex items-center gap-2">
              <Label
                htmlFor="qtd_tentativas"
                className="shrink-0 text-[12px] font-semibold leading-none text-slate-900"
              >
                QTD:
              </Label>
              <Input
                id="qtd_tentativas"
                name="qtd_tentativas"
                type="tel"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={1}
                placeholder="0"
                value={qtdT}
                onChange={(e) => setQtdT(onlyDigits(e.target.value).slice(0, 1))}
                disabled={loading || busy || !bloqueioLogin}
                className="h-10 w-12 rounded-lg border-slate-400 bg-white text-center text-base text-slate-900 shadow-none"
              />
            </div>
          </div>
        </div>

        <div className="mx-auto mt-auto w-full max-w-[320px] pb-2 pt-6">
          <Button
            type="button"
            className={actionBtn3dMd}
            onClick={() => void confirmar()}
            disabled={loading || busy}
          >
            {busy ? 'Salvando…' : 'Confirmar'}
          </Button>
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
