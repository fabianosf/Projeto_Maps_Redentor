import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { cancelChangePassword, changePassword } from '@/api/auth';
import { FormField } from '@/components/forms/FormField';
import { AppDialog } from '@/components/shared/AppDialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { PasswordToggle } from '@/components/shared/PasswordToggle';
import { ScreenLabel } from '@/components/shared/ScreenLabel';
import { Button } from '@/components/ui/button';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import { useFocusInput } from '@/hooks/useFocusInput';
import { useScreenBg } from '@/hooks/useScreenBg';
import { isValidMatricula, validatePassword } from '@/utils/validation';

const SCREEN_BG = '#b9c8d4';

type LocationState = { changeToken?: string; matricula?: string };

export function CadastroSenhaScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as LocationState | null) ?? {};
  const changeToken = state.changeToken ?? '';
  const matricula = state.matricula ?? '';

  const novaSenhaRef = useFocusInput<HTMLInputElement>(true);
  const confirmacaoRef = useRef<HTMLInputElement>(null);

  const [novaSenha, setNovaSenha] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [showNova, setShowNova] = useState(false);
  const [showConf, setShowConf] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modalMsg, setModalMsg] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useScreenBg(SCREEN_BG);

  useEffect(() => {
    if (!changeToken) navigate('/', { replace: true });
  }, [changeToken, navigate]);

  const goLogin = () => navigate('/', { replace: true });

  const onCancelar = async () => {
    if (changeToken) {
      await cancelChangePassword(changeToken).catch(() => undefined);
    }
    goLogin();
  };

  const submitChange = async () => {
    if (submitting || !changeToken) return;

    if (!isValidMatricula(matricula.trim())) {
      setSuccess(false);
      setModalMsg('Matrícula inválida!');
      return;
    }

    const policyError = validatePassword(novaSenha, confirmacao);
    if (policyError) {
      setSuccess(false);
      setModalMsg(policyError);
      return;
    }

    setSubmitting(true);
    try {
      const { response, data } = await changePassword(
        changeToken,
        novaSenha,
        confirmacao,
      );

      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        setSuccess(false);
        setModalMsg(
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : 'Operação não autorizada.',
        );
        return;
      }

      setSuccess(true);
      setModalMsg(
        'mensagem' in data && data.mensagem
          ? data.mensagem
          : 'Senha cadastrada com sucesso!',
      );
    } catch {
      setSuccess(false);
      setModalMsg('Falha ao cadastrar senha. Tente novamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitChange();
  };

  if (!changeToken) return null;

  return (
    <div className="page flex min-h-dvh flex-col bg-[#b9c8d4]">
      <PageHeader
        title="CADASTRO DE SENHA"
        onBack={() => void onCancelar()}
      />

      <div className="page-body flex-1 bg-[#b9c8d4]">
        <form
          className="mx-auto mt-2 w-full max-w-[340px] field-stack"
          onSubmit={onSubmit}
          autoComplete="off"
          noValidate
        >
          {matricula ? (
            <FormField
              label="Matrícula"
              name="matricula"
              type="text"
              value={matricula}
              readOnly
              disabled
            />
          ) : null}

          <FormField
            ref={novaSenhaRef}
            label="Digite a nova senha"
            name="nova_senha"
            type={showNova ? 'text' : 'password'}
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            placeholder="Mínimo 8 caracteres"
            enterKeyHint="next"
            onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                confirmacaoRef.current?.focus();
              }
            }}
            rightSlot={
              <PasswordToggle visible={showNova} onToggle={() => setShowNova((v) => !v)} />
            }
          />

          <FormField
            ref={confirmacaoRef}
            label="Confirme a nova senha"
            name="confirmacao_senha"
            type={showConf ? 'text' : 'password'}
            value={confirmacao}
            onChange={(e) => setConfirmacao(e.target.value)}
            placeholder="Repita a senha"
            enterKeyHint="done"
            onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                void submitChange();
              }
            }}
            rightSlot={
              <PasswordToggle visible={showConf} onToggle={() => setShowConf((v) => !v)} />
            }
          />

          <div className="mt-4 grid grid-cols-2 gap-3">
            <Button type="submit" className={actionBtn3dMd}>
              Confirmar
            </Button>
            <Button
              type="button"
              className={actionBtn3dMd}
              onClick={() => void onCancelar()}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </div>

      <ScreenLabel text="Tela 02 — Cadastro de senha" />

      <AppDialog
        open={modalMsg !== null}
        message={modalMsg ?? ''}
        onConfirm={() => {
          setModalMsg(null);
          if (success) {
            toast.success('Senha cadastrada. Faça login novamente.');
            goLogin();
          }
        }}
      />
    </div>
  );
}
