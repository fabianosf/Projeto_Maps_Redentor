import {
  useCallback,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User } from 'lucide-react';
import { login, cancelLogin } from '@/api/auth';
import { FormField } from '@/components/forms/FormField';
import { AppDialog } from '@/components/shared/AppDialog';
import { Logo } from '@/components/shared/Logo';
import { PageHeader } from '@/components/shared/PageHeader';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { Button } from '@/components/ui/button';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { isValidMatricula, isValidPasswordFormat, MATRICULA_MAX_LENGTH, onlyMatriculaDigits } from '@/utils/validation';
import { closeBrowserTabOrReturn } from '@/utils/webNavigation';

const LOGIN_BG = '#b9c8d4';

const LOGIN_INVALID = 'Login inválido!';
const MATRICULA_INVALIDA = 'Matrícula inválida!';
const SENHA_INVALIDA = 'Senha inválida!';
const USUARIO_INVALIDO = 'Usuário inválido!';
const LIMITE_TENTATIVAS = 'Limite máximo de tentativas!';

export function LoginScreen() {
  const navigate = useNavigate();
  const matriculaRef = useFocusInput<HTMLInputElement>(true);
  const senhaRef = useRef<HTMLInputElement>(null);

  const [matricula, setMatricula] = useState('');
  const [senha, setSenha] = useState('');
  const [showSenha, setShowSenha] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMessage, setModalMessage] = useState(LOGIN_INVALID);
  const [clearOnConfirm, setClearOnConfirm] = useState(true);
  const [focusAfterModal, setFocusAfterModal] = useState<'matricula' | 'senha'>('matricula');

  const clearMatriculaOnlyAndFocus = useCallback(() => {
    setMatricula('');
    window.setTimeout(() => matriculaRef.current?.focus(), 0);
  }, [matriculaRef]);

  const clearMatriculaAndFocusSenha = useCallback(() => {
    setMatricula('');
    setSenha('');
    setShowSenha(false);
    window.setTimeout(() => senhaRef.current?.focus(), 0);
  }, []);

  const showError = useCallback(
    (message: string, shouldClear: boolean, focus: 'matricula' | 'senha') => {
      setModalMessage(message);
      setClearOnConfirm(shouldClear);
      setFocusAfterModal(focus);
      setModalOpen(true);
    },
    [],
  );

  const handleMatriculaKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      senhaRef.current?.focus();
      return;
    }
    if (
      e.key.length === 1 &&
      !/[0-9]/.test(e.key) &&
      !e.ctrlKey &&
      !e.metaKey &&
      !e.altKey
    ) {
      e.preventDefault();
    }
  };

  const submitLogin = async () => {
    if (submitting) return;
    const mat = matricula.trim();
    if (!isValidMatricula(mat)) {
      showError(MATRICULA_INVALIDA, true, 'matricula');
      return;
    }
    if (!senha || !isValidPasswordFormat(senha)) {
      showError(SENHA_INVALIDA, true, 'senha');
      return;
    }

    setSubmitting(true);
    try {
      const { response, data } = await login(mat, senha);

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const apiMsg =
          data && 'mensagem' in data && typeof data.mensagem === 'string' && data.mensagem
            ? data.mensagem
            : LOGIN_INVALID;
        const codigo =
          data && 'codigo' in data && typeof data.codigo === 'string' ? data.codigo : '';
        const isDbDown = response.status === 503 || apiMsg.toLowerCase().includes('banco');
        const isLimite = codigo === 'limite_tentativas' || apiMsg === LIMITE_TENTATIVAS;
        const displayMsg = isLimite
          ? LIMITE_TENTATIVAS
          : isDbDown
            ? apiMsg
            : apiMsg ||
              (codigo === 'matricula_invalida'
                ? MATRICULA_INVALIDA
                : codigo === 'usuario_invalido'
                  ? USUARIO_INVALIDO
                  : codigo === 'senha_invalida'
                    ? SENHA_INVALIDA
                    : LOGIN_INVALID);
        const focusSenha =
          codigo === 'senha_invalida' ||
          displayMsg === SENHA_INVALIDA ||
          (!isLimite &&
            !isDbDown &&
            codigo !== 'matricula_invalida' &&
            codigo !== 'usuario_invalido' &&
            apiMsg === SENHA_INVALIDA);
        showError(
          displayMsg,
          !isDbDown && !isLimite,
          isLimite ? 'matricula' : focusSenha ? 'senha' : 'matricula',
        );
        return;
      }

      if (data.trocar_senha) {
        navigate('/cadastro-senha', {
          replace: true,
          state: {
            changeToken: data.change_token ?? '',
            matricula: data.usuario?.matricula ?? mat,
          },
        });
        return;
      }

      navigate('/principal', { replace: true });
    } catch {
      showError(
        'Não foi possível conectar à API. Verifique se o Backend está rodando.',
        false,
        'matricula',
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
    closeBrowserTabOrReturn();
  };

  useScreenBg(LOGIN_BG);

  return (
    <div className="page flex min-h-dvh flex-col bg-[#b9c8d4]">
      <PageHeader title="LOGIN" />

      <div className="page-body-center flex-1 bg-[#b9c8d4]">
        <div className="form-stack bg-transparent">
          <Logo />

          <form className="field-stack mt-2 bg-transparent" onSubmit={onSubmit} autoComplete="off" noValidate>
            <FormField
              ref={matriculaRef}
              label="Matrícula"
              name="matricula"
              type="tel"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={MATRICULA_MAX_LENGTH}
              placeholder="Matrícula"
              autoComplete="username"
              value={matricula}
              onChange={(e) => setMatricula(onlyMatriculaDigits(e.target.value))}
              onKeyDown={handleMatriculaKeyDown}
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

      <AppDialog
        open={modalOpen}
        message={modalMessage}
        onConfirm={() => {
          setModalOpen(false);
          if (clearOnConfirm) {
            if (focusAfterModal === 'senha') clearMatriculaAndFocusSenha();
            else clearMatriculaOnlyAndFocus();
          } else {
            window.setTimeout(() => {
              if (focusAfterModal === 'senha') senhaRef.current?.focus();
              else matriculaRef.current?.focus();
            }, 0);
          }
        }}
      />
    </div>
  );
}
