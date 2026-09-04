import {
  useCallback,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { Lock, User } from 'lucide-react';
import { cancelLogin, login } from '@/api/auth';
import { ApiRequestError } from '@/api/client';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { Logo } from '@/components/shared/Logo';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import {
  isValidMatricula,
  isValidPasswordFormat,
} from '@/utils/validation';

const LOGIN_BG = '#b9c8d4';

const MATRICULA_INVALIDA = 'Matrícula inválida!';
const SENHA_INVALIDA = 'Senha inválida!';
const USUARIO_INVALIDO = 'Usuário inválido!';
const LIMITE_TENTATIVAS = 'Limite máximo de tentativas!';

type FocusField = 'matricula' | 'senha';

type ModalState = {
  open: boolean;
  message: string;
  clearField: FocusField | null;
};

const MODAL_CLOSED: ModalState = {
  open: false,
  message: '',
  clearField: null,
};

export function LoginScreen() {
  const navigate = useNavigate();
  const { user, loading, setSessionFromUsuario, clearSession } = useAuth();
  const matriculaRef = useFocusInput<HTMLInputElement>(!loading && !user);
  const senhaRef = useRef<HTMLInputElement>(null);

  const [matricula, setMatricula] = useState('');
  const [senha, setSenha] = useState('');
  const [showSenha, setShowSenha] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modal, setModal] = useState<ModalState>(MODAL_CLOSED);

  const showError = useCallback((message: string, clearField: FocusField | null) => {
    setModal({ open: true, message, clearField });
  }, []);

  const handleModalOk = useCallback(() => {
    const field = modal.clearField;
    setModal(MODAL_CLOSED);
    if (field === 'matricula') {
      setMatricula('');
      window.setTimeout(() => matriculaRef.current?.focus(), 0);
    } else if (field === 'senha') {
      setSenha('');
      setShowSenha(false);
      window.setTimeout(() => senhaRef.current?.focus(), 0);
    }
  }, [modal.clearField, matriculaRef]);

  const submitLogin = async () => {
    if (submitting) return;

    const mat = matricula.trim();
    if (!isValidMatricula(mat)) {
      showError(MATRICULA_INVALIDA, 'matricula');
      return;
    }
    if (!senha || !isValidPasswordFormat(senha)) {
      showError(SENHA_INVALIDA, 'senha');
      return;
    }

    setSubmitting(true);
    try {
      const data = await login(mat, senha);

      if (data.trocar_senha) {
        navigate('/primeiro-acesso', {
          replace: true,
          state: {
            changeToken: data.change_token ?? '',
            matricula: data.usuario.matricula,
          },
        });
        return;
      }

      setSessionFromUsuario(data.usuario);
      navigate('/principal', { replace: true });
    } catch (err) {
      if (err instanceof ApiRequestError) {
        const codigo = err.body.codigo ?? '';
        const apiMsg = err.body.mensagem || '';
        const isDbDown =
          err.status === 503 || apiMsg.toLowerCase().includes('banco');
        const isLimite =
          codigo === 'limite_tentativas' || apiMsg === LIMITE_TENTATIVAS;

        if (isLimite) {
          showError(LIMITE_TENTATIVAS, null);
          return;
        }
        if (isDbDown) {
          showError(apiMsg || 'Serviço indisponível.', null);
          return;
        }
        if (codigo === 'usuario_invalido' || apiMsg === USUARIO_INVALIDO) {
          showError(USUARIO_INVALIDO, 'matricula');
          return;
        }
        if (codigo === 'matricula_invalida' || apiMsg === MATRICULA_INVALIDA) {
          showError(MATRICULA_INVALIDA, 'matricula');
          return;
        }
        if (codigo === 'senha_invalida' || apiMsg === SENHA_INVALIDA) {
          showError(SENHA_INVALIDA, 'senha');
          return;
        }
        showError(apiMsg || SENHA_INVALIDA, 'senha');
        return;
      }

      showError(
        'Não foi possível conectar à API. Verifique se o Backend está rodando.',
        null,
      );
    } finally {
      setSubmitting(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitLogin();
  };

  const handleCancelar = () => {
    void cancelLogin().catch(() => undefined);
    clearSession();
    window.history.back();
  };

  const onMatriculaKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      senhaRef.current?.focus();
    }
  };

  useScreenBg(LOGIN_BG);

  if (loading) return <LoadingState />;
  if (user) return <Navigate to="/principal" replace />;

  return (
    <AppShell className="bg-[#b9c8d4]">
      <div className="page flex min-h-dvh flex-col bg-[#b9c8d4]">
        <PageHeader title="LOGIN" />

        <div className="page-body-center flex-1 bg-[#b9c8d4]">
          <div className="form-stack bg-transparent">
            <Logo />

            <form
              className="field-stack mt-2 bg-transparent"
              onSubmit={onSubmit}
              autoComplete="off"
              noValidate
            >
              <FormField
                ref={matriculaRef}
                label="Matrícula"
                name="matricula"
                type="text"
                inputMode="numeric"
                placeholder="Matrícula"
                autoComplete="username"
                value={matricula}
                onChange={(e) => setMatricula(e.target.value)}
                onKeyDown={onMatriculaKeyDown}
                leftIcon={<User className="h-4 w-4" />}
                enterKeyHint="next"
              />

              <FormField
                ref={senhaRef}
                label="Senha"
                name="senha"
                type={showSenha ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    void submitLogin();
                  }
                }}
                leftIcon={<Lock className="h-4 w-4" />}
                rightSlot={
                  <PasswordToggle
                    visible={showSenha}
                    onToggle={() => setShowSenha((v) => !v)}
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
                  onClick={handleCancelar}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </div>
        </div>

        <AlertDialog
          open={modal.open}
          message={modal.message}
          onConfirm={handleModalOk}
        />
      </div>
    </AppShell>
  );
}
