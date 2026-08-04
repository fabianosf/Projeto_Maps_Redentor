import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User } from 'lucide-react';
import { login } from '@/api/auth';
import { FormField } from '@/components/forms/FormField';
import { AppDialog } from '@/components/shared/AppDialog';
import { Logo } from '@/components/shared/Logo';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { ScreenLabel } from '@/components/shared/ScreenLabel';
import { Button } from '@/components/ui/button';
import { useFocusInput } from '@/hooks/useFocusInput';
import { onlyDigits } from '@/utils/validation';

const LOGIN_BG = '#b9c8d4';

const LOGIN_INVALID = 'Login inválido!';

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

  const clearAndFocusMatricula = useCallback(() => {
    setMatricula('');
    setSenha('');
    setShowSenha(false);
    window.setTimeout(() => matriculaRef.current?.focus(), 0);
  }, [matriculaRef]);

  const showError = useCallback((message: string, shouldClear: boolean) => {
    setModalMessage(message);
    setClearOnConfirm(shouldClear);
    setModalOpen(true);
  }, []);

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
    if (!mat || !senha) {
      showError(LOGIN_INVALID, true);
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
        const isDbDown = response.status === 503 || apiMsg.toLowerCase().includes('banco');
        showError(isDbDown ? apiMsg : LOGIN_INVALID, !isDbDown);
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

      navigate('/lista-mapa', { replace: true });
    } catch {
      showError(
        'Não foi possível conectar à API. Verifique se o Backend está rodando.',
        false,
      );
    } finally {
      setSubmitting(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitLogin();
  };

  // Fundo uniforme na Login (html/body/shell) — preenche áreas ao redor do logo transparente
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const shell = document.querySelector('.app-shell') as HTMLElement | null;
    const prevHtml = html.style.backgroundColor;
    const prevBody = body.style.backgroundColor;
    const prevShell = shell?.style.backgroundColor ?? '';
    html.style.backgroundColor = LOGIN_BG;
    body.style.backgroundColor = LOGIN_BG;
    if (shell) shell.style.backgroundColor = LOGIN_BG;
    return () => {
      html.style.backgroundColor = prevHtml;
      body.style.backgroundColor = prevBody;
      if (shell) shell.style.backgroundColor = prevShell;
    };
  }, []);

  return (
    <div className="page min-h-dvh bg-[#b9c8d4]">
      <div className="page-body-center bg-[#b9c8d4]">
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
              placeholder="Matrícula"
              autoComplete="username"
              value={matricula}
              onChange={(e) => setMatricula(onlyDigits(e.target.value))}
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
              <Button type="submit" className="w-full" disabled={submitting}>
                Confirmar
              </Button>
              <Button
                type="button"
                className="w-full"
                onClick={clearAndFocusMatricula}
                disabled={submitting}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </div>
      </div>

      <ScreenLabel text="Tela 01 — Login" />

      <AppDialog
        open={modalOpen}
        message={modalMessage}
        onConfirm={() => {
          setModalOpen(false);
          if (clearOnConfirm) clearAndFocusMatricula();
          else window.setTimeout(() => matriculaRef.current?.focus(), 0);
        }}
      />
    </div>
  );
}
