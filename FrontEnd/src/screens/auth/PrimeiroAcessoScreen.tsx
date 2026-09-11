import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Loader2, Lock } from 'lucide-react';
import { cancelChangePassword, changePassword, login } from '@/api/auth';
import { ApiRequestError } from '@/api/client';
import { AlertDialog } from '@/components/AlertDialog';
import { AuthShell } from '@/components/auth/AuthShell';
import { DsAlert } from '@/components/auth/DsAlert';
import { PasswordStrength } from '@/components/auth/PasswordStrength';
import { FormField } from '@/components/FormField';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { AUTH_BG } from '@/theme/tokens';
import { validarPoliticaSenha } from '@/utils/validacoes';

const SENHA_INVALIDA = 'Senha inválida!';
const SENHAS_DIFERENTES = 'Senhas digitadas diferentes!';
const SUCESSO = 'Senha cadastrada com sucesso!';

type LocationState = {
  changeToken?: string;
  matricula?: string;
};

type Mode = 'form' | 'success';

/**
 * Criação / redefinição de senha (primeiro acesso ou após reset).
 * Nunca exibe nem loga o valor da senha.
 */
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
  const [mode, setMode] = useState<Mode>('form');
  const [matchError, setMatchError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMessage, setModalMessage] = useState(SENHA_INVALIDA);

  useScreenBg(AUTH_BG);

  useEffect(() => {
    if (!changeToken) {
      navigate('/login', { replace: true });
    }
  }, [changeToken, navigate]);

  const showError = useCallback((message: string) => {
    setFormError(message);
    setModalMessage(message);
    setModalOpen(true);
  }, []);

  const handleModalOk = useCallback(() => {
    setModalOpen(false);
    if (mode === 'success') return;
    setNovaSenha('');
    setConfirmacao('');
    setShowNova(false);
    setShowConf(false);
    setMatchError(null);
    window.setTimeout(() => novaSenhaRef.current?.focus(), 0);
  }, [mode, novaSenhaRef]);

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

  const concluirSucesso = async () => {
    setSubmitting(true);
    try {
      const loginData = await login(matricula, novaSenha);
      if (loginData.trocar_senha) {
        showError(SENHA_INVALIDA);
        setMode('form');
        return;
      }
      setSessionFromUsuario(loginData.usuario);
      navigate('/principal', { replace: true });
    } catch {
      // Senha já foi alterada — volta ao login sem expor valor.
      navigate('/login', { replace: true });
    } finally {
      setSubmitting(false);
    }
  };

  const submitChange = async () => {
    if (submitting || !changeToken) return;
    setFormError(null);

    if (novaSenha !== confirmacao) {
      setMatchError(SENHAS_DIFERENTES);
      showError(SENHAS_DIFERENTES);
      return;
    }
    setMatchError(null);

    if (!validarPoliticaSenha(novaSenha)) {
      showError(SENHA_INVALIDA);
      return;
    }

    setSubmitting(true);
    try {
      await changePassword(changeToken, novaSenha, confirmacao);
      setMode('success');
      setModalMessage(SUCESSO);
      setModalOpen(true);
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

  const onConfirmChange = (value: string) => {
    setConfirmacao(value);
    if (!value) {
      setMatchError(null);
      return;
    }
    setMatchError(value !== novaSenha ? SENHAS_DIFERENTES : null);
  };

  if (!changeToken) return null;

  if (mode === 'success') {
    return (
      <AuthShell title="Senha atualizada" subtitle="Tudo certo para continuar">
        <div className="surface-card space-y-4 p-6">
          <DsAlert tone="success" title="Cadastro concluído">
            Sua nova senha foi salva. Toque em continuar para entrar no
            aplicativo.
          </DsAlert>
          <Button
            type="button"
            className="ds-cta"
            disabled={submitting}
            onClick={() => void concluirSucesso()}
          >
            {submitting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                Entrando…
              </>
            ) : (
              'Continuar'
            )}
          </Button>
        </div>
        <AlertDialog
          open={modalOpen}
          message={modalMessage}
          onConfirm={() => {
            setModalOpen(false);
            void concluirSucesso();
          }}
        />
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Criar nova senha"
      subtitle={
        matricula
          ? `Defina a senha definitiva da matrícula ${matricula}`
          : 'Defina sua senha definitiva'
      }
    >
      <div className="surface-card p-6">
        <form className="field-stack" onSubmit={onSubmit} autoComplete="off" noValidate>
          {formError && !matchError ? (
            <DsAlert tone="error">{formError}</DsAlert>
          ) : null}

          <FormField
            ref={novaSenhaRef}
            label="Nova senha"
            name="nova_senha"
            type={showNova ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="new-password"
            value={novaSenha}
            onChange={(e) => {
              setNovaSenha(e.target.value);
              if (confirmacao) {
                setMatchError(
                  e.target.value !== confirmacao ? SENHAS_DIFERENTES : null,
                );
              }
            }}
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

          <PasswordStrength password={novaSenha} />

          <FormField
            ref={confirmacaoRef}
            label="Confirmar senha"
            name="confirmacao_senha"
            type={showConf ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="new-password"
            value={confirmacao}
            onChange={(e) => onConfirmChange(e.target.value)}
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
            error={matchError ?? undefined}
            enterKeyHint="done"
          />

          <div className="flex flex-col gap-3 pt-1">
            <Button type="submit" className="ds-cta" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Salvando…
                </>
              ) : (
                'Salvar senha'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="ds-cta"
              onClick={onCancelar}
              disabled={submitting}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </div>

      <AlertDialog
        open={modalOpen}
        message={modalMessage}
        onConfirm={handleModalOk}
      />
    </AuthShell>
  );
}
