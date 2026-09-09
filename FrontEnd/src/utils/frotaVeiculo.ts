/**
 * Regras oficiais de frota por empresa (alinhado a BackEnd/cadastros_service.py).
 * Formato: 1 letra maiúscula + 5 dígitos (6 caracteres).
 * - Redentor: C47NNN  (^C47\d{3}$)
 * - Futuro:   C30NNN  (^C30\d{3}$)
 * - Barra:    D13NNN  (^D13\d{3}$)
 */

export type FrotaRegra = {
  /** Prefixo fixo (letra + código), ex.: C47 */
  codigo: string;
  regex: RegExp;
  /** Guia visual sem preencher o sufixo, ex.: C47___ */
  mascara: string;
  exemplo: string;
  mensagem: string;
  placeholder: string;
};

const REGRAS: Record<string, FrotaRegra> = {
  redentor: {
    codigo: 'C47',
    regex: /^C47\d{3}$/,
    mascara: 'C47___',
    exemplo: 'C47654',
    mensagem: 'Informe no formato C47 + 3 números. Ex.: C47654.',
    placeholder: 'Ex.: C47654',
  },
  futuro: {
    codigo: 'C30',
    regex: /^C30\d{3}$/,
    mascara: 'C30___',
    exemplo: 'C30114',
    mensagem: 'Informe no formato C30 + 3 números. Ex.: C30114.',
    placeholder: 'Ex.: C30114',
  },
  barra: {
    codigo: 'D13',
    regex: /^D13\d{3}$/,
    mascara: 'D13___',
    exemplo: 'D13450',
    mensagem: 'Informe no formato D13 + 3 números. Ex.: D13450.',
    placeholder: 'Ex.: D13450',
  },
};

export function normalizarFrotaDigitada(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 6);
}

export function chaveEmpresa(descricao: string | null | undefined): string {
  return String(descricao ?? '')
    .trim()
    .toLowerCase();
}

export function regraFrotaEmpresa(
  empresaDescricao: string | null | undefined,
): FrotaRegra | null {
  return REGRAS[chaveEmpresa(empresaDescricao)] ?? null;
}

/** Prefixo fixo da empresa (C47 / C30 / D13). */
export function prefixoFrotaEmpresa(
  empresaDescricao: string | null | undefined,
): string | null {
  return regraFrotaEmpresa(empresaDescricao)?.codigo ?? null;
}

export function mascaraGuiaFrotaEmpresa(
  empresaDescricao: string | null | undefined,
): string | null {
  return regraFrotaEmpresa(empresaDescricao)?.mascara ?? null;
}

export function placeholderFrotaEmpresa(
  empresaDescricao: string | null | undefined,
): string {
  return regraFrotaEmpresa(empresaDescricao)?.placeholder ?? 'Ex.: letra + 5 dígitos';
}

/** @deprecated use placeholderFrotaEmpresa / mascaraGuiaFrotaEmpresa */
export function exemploFrotaEmpresa(
  empresaDescricao: string | null | undefined,
): string {
  const regra = regraFrotaEmpresa(empresaDescricao);
  if (!regra) return 'letra + 5 dígitos';
  return regra.exemplo;
}

/**
 * Digitação parcial compatível com o padrão (ex.: "C", "C3", "C30", "C301").
 * Não exige os 6 caracteres completos.
 */
export function frotaParcialCompativel(
  numeroFrota: string,
  empresaDescricao: string | null | undefined,
): boolean {
  const frota = String(numeroFrota ?? '').trim().toUpperCase();
  if (!frota) return true;
  const regra = regraFrotaEmpresa(empresaDescricao);
  if (!regra) return false;
  if (frota.length > 6) return false;
  if (frota.length <= regra.codigo.length) {
    return regra.codigo.startsWith(frota);
  }
  if (!frota.startsWith(regra.codigo)) return false;
  const resto = frota.slice(regra.codigo.length);
  return /^\d{0,3}$/.test(resto);
}

/**
 * Valida frota completa para a empresa.
 * Retorna mensagem de erro em português ou null se ok.
 */
export function validarFrotaParaEmpresa(
  numeroFrota: string,
  empresaDescricao: string | null | undefined,
): string | null {
  const frota = String(numeroFrota ?? '').trim().toUpperCase();
  const regra = regraFrotaEmpresa(empresaDescricao);

  if (!regra) {
    return empresaDescricao
      ? `Empresa "${empresaDescricao}" sem padrão de frota configurado.`
      : 'Selecione a empresa.';
  }

  if (!frota) return regra.mensagem;

  if (!regra.regex.test(frota)) {
    return regra.mensagem;
  }

  return null;
}

/**
 * Erro para exibir durante a digitação (parcial ou completo).
 * Vazio → sem erro (a obrigatoriedade é no Confirmar).
 */
export function erroFrotaDuranteDigitacao(
  numeroFrota: string,
  empresaDescricao: string | null | undefined,
): string | null {
  const frota = String(numeroFrota ?? '').trim().toUpperCase();
  if (!frota) return null;
  if (frota.length < 6) {
    return frotaParcialCompativel(frota, empresaDescricao)
      ? null
      : validarFrotaParaEmpresa(frota, empresaDescricao);
  }
  return validarFrotaParaEmpresa(frota, empresaDescricao);
}

export function frotaFormatoBasicoOk(frota: string): boolean {
  const t = String(frota ?? '').trim().toUpperCase();
  return /^[A-Z]\d{5}$/.test(t);
}
