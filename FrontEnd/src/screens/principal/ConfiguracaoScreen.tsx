import { useCallback, useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import { BarChart3, UserCog } from 'lucide-react';

import { getQtdTentativas, saveQtdTentativas } from '@/api/config';

import { me } from '@/api/auth';

import { AppDialog } from '@/components/shared/AppDialog';

import { PageHeader } from '@/components/shared/PageHeader';

import { ScreenLabel } from '@/components/shared/ScreenLabel';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { useScreenBg } from '@/hooks/useScreenBg';

import { actionBtn3dBase, actionBtn3dMd } from '@/lib/actionBtn3d';
import { cn } from '@/lib/utils';
import { canAccessConfiguracao } from '@/utils/perfilAccess';
import { onlyDigits } from '@/utils/validation';



const BG = '#B9C8D4';

const configToolbarBtnClass = cn(
  actionBtn3dBase,
  'flex h-[calc(39px+3mm)] w-[calc(88px+1.5cm)] shrink-0 flex-row gap-1.5 px-2 text-[11px] normal-case',
);



/** Tela de Configuração — acessos administrativos e parâmetros. */

export function ConfiguracaoScreen() {

  const navigate = useNavigate();

  useScreenBg(BG);



  const [allowed, setAllowed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [qtdT, setQtdT] = useState('');
  const [bloqueioLogin, setBloqueioLogin] = useState(true);

  const [busy, setBusy] = useState(false);

  const [infoMsg, setInfoMsg] = useState<string | null>(null);



  const carregar = useCallback(async () => {

    setLoading(true);

    try {

      const { response, data } = await getQtdTentativas();

      if (response.ok && data && 'ok' in data && data.ok === true) {

        setQtdT(String(data.valor ?? ''));

        setBloqueioLogin(data.bloqueio_tentativas !== false);

      }

    } catch {

      setInfoMsg('Falha ao carregar Qtd/Tentativas de login.');

    } finally {

      setLoading(false);

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

        const perfil = data.usuario.codigo_perfil;

        if (!canAccessConfiguracao(perfil)) {

          navigate('/principal', { replace: true });

          return;

        }

        if (!cancelled) {
          setAllowed(true);
          await carregar();
        }

      } catch {

        navigate('/', { replace: true });

      }

    })();

    return () => {

      cancelled = true;

    };

  }, [carregar, navigate]);



  const confirmar = async () => {

    if (busy || loading || !allowed) return;



    const valor = qtdT.trim();

    if (!valor) {

      setInfoMsg('Informe a quantidade de tentativas de login.');

      return;

    }



    setBusy(true);

    try {

      const { response, data } = await saveQtdTentativas(valor, bloqueioLogin);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {

        const msg =

          data && 'mensagem' in data && data.mensagem

            ? data.mensagem

            : 'Não foi possível salvar Qtd/Tentativas de login.';

        setInfoMsg(msg);

        return;

      }

      setQtdT(String(data.valor));

      if (data.bloqueio_tentativas != null) {
        setBloqueioLogin(data.bloqueio_tentativas);
      }

      setInfoMsg('Configurações de login atualizadas.');

    } catch {

      setInfoMsg('Falha de comunicação com a API.');

    } finally {

      setBusy(false);

    }

  };



  return (

    <div className="page flex h-dvh max-h-dvh flex-col overflow-hidden bg-[#B9C8D4] text-slate-900">

      <PageHeader title="CONFIGURAÇÃO" onBack={() => navigate('/principal')} />



      <div className="flex min-h-0 flex-1 flex-col bg-[#B9C8D4] px-4 py-8">

        {allowed ? (

          <>

            <div className="mx-auto flex w-full max-w-[360px] flex-col gap-6">

              <div className="flex w-full items-start justify-center gap-[2.5cm] px-1">

                <Button

                  type="button"

                  className={configToolbarBtnClass}

                  onClick={() => navigate('/cadastro-usuario')}

                  disabled={busy || loading}

                >

                  <UserCog className="h-4 w-4 shrink-0" strokeWidth={2.25} />

                  <span className="normal-case leading-tight text-[10px]">

                    Cadastro de usuários

                  </span>

                </Button>

                <Button

                  type="button"

                  className={configToolbarBtnClass}

                  onClick={() => navigate('/indicadores')}

                  disabled={busy || loading}

                >

                  <BarChart3 className="h-4 w-4 shrink-0" strokeWidth={2.25} />

                  <span className="normal-case leading-tight text-[10px]">Indicadores</span>

                </Button>

              </div>



              <hr className="border-0 border-t-2 border-black" />



              <div className="flex w-full flex-col gap-1.5 self-start px-1">
                <label className="flex items-center gap-2 text-[12px] font-normal leading-snug text-slate-900">
                  <input
                    type="checkbox"
                    checked={bloqueioLogin}
                    onChange={(e) => setBloqueioLogin(e.target.checked)}
                    disabled={loading || busy}
                    className="h-4 w-4 shrink-0 accent-[#1e3a5f]"
                  />
                  Login (Bloqueio de tentativas de acesso):
                </label>
                <div className="mt-1 flex items-center gap-2">
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
                    onChange={(e) =>
                      setQtdT(onlyDigits(e.target.value).slice(0, 1))
                    }
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

          </>

        ) : loading ? (
          <p className="mx-auto max-w-[320px] text-center text-[15px] font-medium text-slate-800">
            Carregando…
          </p>
        ) : null}

      </div>



      <AppDialog

        open={infoMsg !== null}

        message={infoMsg ?? ''}

        confirmLabel="OK"

        onConfirm={() => setInfoMsg(null)}

      />



      <ScreenLabel text="Tela Configuração" />

    </div>

  );

}

