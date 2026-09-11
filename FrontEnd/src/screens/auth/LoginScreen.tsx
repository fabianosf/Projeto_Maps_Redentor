import {
  useCallback,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Loader2, Lock, User } from 'lucide-react';
import { cancelLogin, login } from '@/api/auth';
import { ApiRequestError } from '@/api/client';
import { AlertDialog } from '@/components/AlertDialog';
import { AuthShell } from '@/components/auth/AuthShell';
import { DsAlert } from '@/components/auth/DsAlert';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { AUTH_BG } from '@/theme/tokens';
import { isValidMatricula } from '@/utils/validation';

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
  const [errMat, setErrMat] = useState<string | null>(null);
  const [errSenha, setErrSenha] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>(MODAL_CLOSED);

  const showError = useCallback((message: string, clearField: FocusField | null) => {
    if (clearField === 'matricula') {
      setErrMat(message);
      setErrSenha(null);
    } else if (clearField === 'senha') {
      setErrSenha(message);
      setErrMat(null);
    } else {
      setBanner(message);
      setErrMat(null);
      setErrSenha(null);
    }
    setModal({ open: true, message, clearField });
  }, []);

  const handleModalOk = useCallback(() => {
    const field = modal.clearField;
    setModal(MODAL_CLOSED);
    if (field === 'matricula') {
      setMatricula('');
      setErrMat(null);
      window.setTimeout(() => matriculaRef.current?.focus(), 0);
    } else if (field === 'senha') {
      setSenha('');
      setShowSenha(false);
      setErrSenha(null);
      window.setTimeout(() => senhaRef.current?.focus(), 0);
    }
  }, [modal.clearField, matriculaRef]);

  const submitLogin = async () => {
    if (submitting) return;
    setBanner(null);

    const mat = matricula.trim();
    if (!isValidMatricula(mat)) {
      showError(MATRICULA_INVALIDA, 'matricula');
      return;
    }
    if (!senha) {
      showError(SENHA_INVALIDA, 'senha');
      return;
    }

    setErrMat(null);
    setErrSenha(null);
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

  useScreenBg(AUTH_BG);

  if (loading) return <LoadingState />;
  if (user) return <Navigate to="/principal" replace />;

  return (
    <AuthShell subtitle="Acesse com sua matrícula operacional">
      <div className={uiCard}>
        <form className="field-stack" onSubmit={onSubmit} autoComplete="off" noValidate>
          {banner ? <DsAlert tone="error">{banner}</DsAlert> : null}

          <FormField
            ref={matriculaRef}
            label="Matrícula"
            name="matricula"
            type="text"
            inputMode="numeric"
            placeholder="Até 5 dígitos"
            autoComplete="username"
            value={matricula}
            onChange={(e) => {
              setMatricula(e.target.value);
              if (errMat) setErrMat(null);
            }}
            onKeyDown={onMatriculaKeyDown}
            leftIcon={<User className="h-4 w-4" />}
            error={errMat ?? undefined}
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
            onChange={(e) => {
              setSenha(e.target.value);
              if (errSenha) setErrSenha(null);
            }}
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
            error={errSenha ?? undefined}
            enterKeyHint="done"
          />

          <div className="flex justify-end">
            <Link
              to="/recuperar-senha"
              className="min-h-touch text-sm font-semibold text-primary underline-offset-2 hover:underline"
            >
              Esqueci minha senha
            </Link>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            <Button type="submit" className="ds-cta" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Entrando…
                </>
              ) : (
                'Entrar'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="ds-cta"
              onClick={handleCancelar}
              disabled={submitting}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </div>

      <AlertDialog
        open={modal.open}
        message={modal.message}
        onConfirm={handleModalOk}
      />
    </AuthShell>
  );
}

const uiCard = 'surface-card p-6';
