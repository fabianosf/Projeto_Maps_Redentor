import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User } from 'lucide-react';
import { AuthShell } from '@/components/auth/AuthShell';
import { DsAlert } from '@/components/auth/DsAlert';
import { FormField } from '@/components/FormField';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import { AUTH_BG } from '@/theme/tokens';
import { isValidMatricula } from '@/utils/validation';

/**
 * Recuperação de senha — fluxo institucional via administrador.
 * Não inventa API; preserva regra: reset gera senha temporária e força troca.
 */
export function RecuperarSenhaScreen() {
  const navigate = useNavigate();
  useScreenBg(AUTH_BG);

  const [matricula, setMatricula] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviado, setEnviado] = useState(false);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const mat = matricula.trim();
    if (!isValidMatricula(mat)) {
      setErro('Informe uma matrícula válida (até 5 dígitos).');
      setEnviado(false);
      return;
    }
    setErro(null);
    setEnviado(true);
  };

  return (
    <AuthShell
      title="Esqueci minha senha"
      subtitle="Recuperação com apoio do administrador"
    >
      <div className="auth-card space-y-4 p-6">
        {enviado ? (
          <>
            <DsAlert tone="success" title="Solicitação registrada">
              Procure o administrador ou inspetor responsável para resetar a
              senha da matrícula informada. Você receberá uma senha temporária
              e, no próximo acesso, deverá criar uma nova.
            </DsAlert>
            <DsAlert tone="info">
              Por segurança, a senha temporária nunca é exibida neste aplicativo
              após o uso.
            </DsAlert>
            <Button
              type="button"
              variant="primary"
              className="ds-cta"
              onClick={() => navigate('/login', { replace: true })}
            >
              Voltar ao login
            </Button>
          </>
        ) : (
          <form className="field-stack" onSubmit={onSubmit} noValidate>
            <DsAlert tone="info">
              Informe sua matrícula. O reset é feito pelo administrador do
              sistema (Cadastro de Usuários → Reset de senha).
            </DsAlert>

            <FormField
              label="Matrícula"
              name="matricula"
              type="text"
              inputMode="numeric"
              placeholder="Até 5 dígitos"
              autoComplete="username"
              value={matricula}
              onChange={(e) => {
                setMatricula(e.target.value);
                if (erro) setErro(null);
              }}
              leftIcon={<User className="h-4 w-4" />}
              error={erro ?? undefined}
            />

            <Button type="submit" variant="primary" className="ds-cta">
              Continuar
            </Button>
            <div className="flex justify-center">
              <Link
                to="/login"
                className="link-cyan inline-flex min-h-touch items-center text-sm font-semibold"
              >
                Voltar ao login
              </Link>
            </div>
          </form>
        )}
      </div>
    </AuthShell>
  );
}
