/**
 * Validações reutilizáveis do FrontEnd RedMapa.
 * Nunca logar senha (nem hash) no console.
 */

/** Caractere gráfico / especial alinhado ao BackEnd (auth_service._PASSWORD_POLICY). */
const CARACTERE_GRAFICO = /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\;/`~]/;

/**
 * Política de senha definitiva (RF-03 / RF-14 / RF-RN-007) — Tela 02:
 * - mínimo 8 caracteres
 * - pelo menos 1 maiúscula
 * - pelo menos 1 minúscula
 * - pelo menos 1 número
 * - pelo menos 1 caractere especial
 */
export function validarPoliticaSenha(senha: string): boolean {
  if (senha.length < 8) return false;
  if (!/[A-Z]/.test(senha)) return false;
  if (!/[a-z]/.test(senha)) return false;
  if (!/\d/.test(senha)) return false;
  if (!CARACTERE_GRAFICO.test(senha)) return false;
  return true;
}
