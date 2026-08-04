/** RF-RN-007 — política de senha definitiva. */
const PASSWORD_POLICY =
  /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]).{8,}$/;

/** Nome: letras, números e espaços (inclui acentos). */
const NOME_ALFANUM = /^[A-Za-zÀ-ÿ0-9\s]+$/;

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, '');
}

export function isNumericMatricula(value: string): boolean {
  return /^\d+$/.test(value);
}

export function isAlphanumericName(value: string): boolean {
  const t = value.trim();
  return t.length > 0 && NOME_ALFANUM.test(t);
}

export function validatePassword(nova: string, confirmacao: string): string | null {
  if (nova !== confirmacao) return 'Senhas digitadas diferentes!';
  if (!PASSWORD_POLICY.test(nova)) {
    return 'Senha inválida! Use alfanumérica, mínimo 8 caracteres e ao menos 1 caractere especial.';
  }
  return null;
}
