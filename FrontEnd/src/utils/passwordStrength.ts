/**
 * Avaliação de senha para UI (força + checklist).
 * Nunca logar o valor da senha.
 */

export type PasswordRequirementId =
  | 'min8'
  | 'upper'
  | 'lower'
  | 'digit'
  | 'special';

export type PasswordRequirement = {
  id: PasswordRequirementId;
  label: string;
  ok: boolean;
};

const SPECIAL = /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\;/`~]/;

export function requisitosSenha(senha: string): PasswordRequirement[] {
  const s = senha ?? '';
  return [
    { id: 'min8', label: 'Mínimo de 8 caracteres', ok: s.length >= 8 },
    { id: 'upper', label: 'Pelo menos 1 letra maiúscula', ok: /[A-Z]/.test(s) },
    { id: 'lower', label: 'Pelo menos 1 letra minúscula', ok: /[a-z]/.test(s) },
    { id: 'digit', label: 'Pelo menos 1 número', ok: /\d/.test(s) },
    {
      id: 'special',
      label: 'Pelo menos 1 caractere especial',
      ok: SPECIAL.test(s),
    },
  ];
}

/** 0–4 conforme requisitos atendidos (agrupado). */
export function forcaSenha(senha: string): 0 | 1 | 2 | 3 | 4 {
  const ok = requisitosSenha(senha).filter((r) => r.ok).length;
  if (ok <= 0) return 0;
  if (ok <= 2) return 1;
  if (ok === 3) return 2;
  if (ok === 4) return 3;
  return 4;
}

export function labelForcaSenha(score: 0 | 1 | 2 | 3 | 4): string {
  switch (score) {
    case 0:
      return 'Vazia';
    case 1:
      return 'Fraca';
    case 2:
      return 'Razoável';
    case 3:
      return 'Boa';
    case 4:
      return 'Forte';
    default:
      return '';
  }
}
