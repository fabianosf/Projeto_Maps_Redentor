import { validarPoliticaSenha } from './validacoes';

/** RF-02 / RF-20 — matrícula numérica, máximo 5 dígitos. */
export const MATRICULA_MAX_LENGTH = 5;

/** RF-20 — nome alfanumérico, máximo 50 caracteres. */
export const NOME_MAX_LENGTH = 50;

/** RF-03 — mesma política da Tela 02, validada no Confirmar do login. */
export function isValidPasswordFormat(value: string): boolean {
  return validarPoliticaSenha(value);
}

/** Nome: letras, números e espaços (inclui acentos). */
const NOME_ALFANUM = /^[A-Za-zÀ-ÿ0-9\s]+$/;

export function onlyDigits(value: string, maxLength?: number): string {
  const digits = value.replace(/\D/g, '');
  if (maxLength != null) {
    return digits.slice(0, maxLength);
  }
  return digits;
}

export function onlyMatriculaDigits(value: string): string {
  return onlyDigits(value, MATRICULA_MAX_LENGTH);
}

export function isValidMatricula(value: string): boolean {
  const t = value.trim();
  return /^\d{1,5}$/.test(t);
}

/** @deprecated Use isValidMatricula — mantém nome usado em telas legadas. */
export function isNumericMatricula(value: string): boolean {
  return isValidMatricula(value);
}

export function isAlphanumericName(value: string): boolean {
  const t = value.trim();
  return t.length > 0 && t.length <= NOME_MAX_LENGTH && NOME_ALFANUM.test(t);
}

export function validatePassword(nova: string, confirmacao: string): string | null {
  if (nova !== confirmacao) return 'Senhas digitadas diferentes!';
  if (!validarPoliticaSenha(nova)) {
    return 'Senha inválida!';
  }
  return null;
}
