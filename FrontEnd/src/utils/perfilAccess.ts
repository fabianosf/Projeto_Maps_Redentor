/** Códigos de perfil — alinhados ao BackEnd (constants.py). */
export const PERFIL_ADMIN = 1;
export const PERFIL_DESPACHANTE = 2;
export const PERFIL_INSPETOR = 3;

/** RN-03 / RF-25 — Tela 09: Administrador e Inspetor; Despachante não acessa. */
export function canAccessConfiguracao(codigoPerfil: number | null | undefined): boolean {
  return codigoPerfil === PERFIL_ADMIN || codigoPerfil === PERFIL_INSPETOR;
}

/** RN-03 — Tela 03: mesmo acesso da Configuração. */
export function canAccessCadastroUsuario(codigoPerfil: number | null | undefined): boolean {
  return canAccessConfiguracao(codigoPerfil);
}

/** RN-03 — Reset de senha: somente Administrador. */
export function canResetSenhaUsuario(codigoPerfil: number | null | undefined): boolean {
  return codigoPerfil === PERFIL_ADMIN;
}
