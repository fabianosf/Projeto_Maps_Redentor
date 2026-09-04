import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { cancelChangePassword, changePassword, login } from '@/api/auth';
import { ApiRequestError } from '@/api/client';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { FormField } from '@/components/FormField';
import { PageHeader } from '@/components/PageHeader';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import { validarPoliticaSenha } from '@/utils/validacoes';

const SCREEN_BG = '#b9c8d4';
const SENHA_INVALIDA = 'Senha inválida!';
const SENHAS_DIFERENTES = 'Senhas digitadas diferentes!';

type LocationState = {
  changeToken?: string;
  matricula?: string;
};

export function PrimeiroAcessoScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setSessionFromUsuario, clearSession } = useAuth();

  const state = (location.state as LocationState | null) ?? {};
  const changeToken = state.changeToken?.trim() ?? '';
  const matricula = state.matricula?.trim() ?? '';

  const novaSenhaRef = useFocusInput<HTMLInputElement>(Boolean(changeToken));
  const confirmacaoRef = useRef<HTMLInputElement>(null);

  const [novaSenha, setNovaSenha] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [showNova, setShowNova] = useState(false);
  const [showConf, setShowConf] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMessage, setModalMessage] = useState(SENHA_INVALIDA);

  useScreenBg(SCREEN_BG);

  useEffect(() => {
    if (!changeToken) {
      navigate('/login', { replace: true });
    }
  }, [changeToken, navigate]);

  const showError = useCallback((message: string) => {
    setModalMessage(message);
    setModalOpen(true);
  }, []);

  const handleModalOk = useCallback(() => {
    setModalOpen(false);
    setNovaSenha('');
    setConfirmacao('');
    setShowNova(false);
    setShowConf(false);
    window.setTimeout(() => novaSenhaRef.current?.focus(), 0);
  }, [novaSenhaRef]);

  const voltarLogin = useCallback(() => {
    clearSession();
    navigate('/login', { replace: true });
  }, [clearSession, navigate]);

  const onCancelar = () => {
    void (async () => {
      if (changeToken) {
        await cancelChangePassword(changeToken).catch(() => undefined);
      }
      voltarLogin();
    })();
  };

  const submitChange = async () => {
    if (submitting || !changeToken) return;

    if (novaSenha !== confirmacao) {
      showError(SENHAS_DIFERENTES);
      return;
    }
    if (!validarPoliticaSenha(novaSenha)) {
      showError(SENHA_INVALIDA);
      return;
    }

    setSubmitting(true);
    try {
      // Endpoint real: POST /api/v1/auth/change-password (não PUT).
      await changePassword(changeToken, novaSenha, confirmacao);

      // Backend limpa o cookie após a troca — autentica de novo sem logar a senha.
      const loginData = await login(matricula, novaSenha);
      if (loginData.trocar_senha) {
        showError(SENHA_INVALIDA);
        return;
      }

      setSessionFromUsuario(loginData.usuario);
      navigate('/principal', { replace: true });
    } catch (err) {
      if (err instanceof ApiRequestError) {
        showError(SENHA_INVALIDA);
        return;
      }
      showError(SENHA_INVALIDA);
    } finally {
      setSubmitting(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitChange();
  };

  const onNovaKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      confirmacaoRef.current?.focus();
    }
  };

  if (!changeToken) return null;

  return (
    <AppShell className="bg-[#b9c8d4]">
      <div className="page flex min-h-dvh flex-col bg-[#b9c8d4]">
        <PageHeader title="CADASTRO DE SENHA" onBack={onCancelar} />

        <div className="page-body-center flex-1 bg-[#b9c8d4]">
          <div className="form-stack bg-transparent">
            <form
              className="field-stack mt-2 bg-transparent"
              onSubmit={onSubmit}
              autoComplete="off"
              noValidate
            >
              <FormField
                ref={novaSenhaRef}
                label="Nova senha"
                name="nova_senha"
                type={showNova ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="new-password"
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                onKeyDown={onNovaKeyDown}
                leftIcon={<Lock className="h-4 w-4" />}
                rightSlot={
                  <PasswordToggle
                    visible={showNova}
                    onToggle={() => setShowNova((v) => !v)}
                  />
                }
                enterKeyHint="next"
              />

              <FormField
                ref={confirmacaoRef}
                label="Confirmar senha"
                name="confirmacao_senha"
                type={showConf ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="new-password"
                value={confirmacao}
                onChange={(e) => setConfirmacao(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    void submitChange();
                  }
                }}
                leftIcon={<Lock className="h-4 w-4" />}
                rightSlot={
                  <PasswordToggle
                    visible={showConf}
                    onToggle={() => setShowConf((v) => !v)}
                  />
                }
                enterKeyHint="done"
              />

              <div className="mt-3 flex flex-col gap-3">
                <Button type="submit" className={actionBtn3dMd}>
                  Confirmar
                </Button>
                <Button
                  type="button"
                  className={actionBtn3dMd}
                  onClick={onCancelar}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </div>
        </div>

        <AlertDialog
          open={modalOpen}
          message={modalMessage}
          onConfirm={handleModalOk}
        />
      </div>
    </AppShell>
  );
}
