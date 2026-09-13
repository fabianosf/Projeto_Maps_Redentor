/**
 * Frota canônica (ADR-08):
 * - Redentor: C47 + 3 dígitos (ex.: C47654)
 * - Futuro:   C30 + 3 dígitos (ex.: C30114)
 * - Barra:    D13 + 3 dígitos (ex.: D13450)
 * Aceita minúsculas na digitação; normaliza/valida/persiste em maiúsculas.
 * Alinhado a BackEnd/cadastros_service.py.
 */

export type FrotaRegra = {
  regex: RegExp;
  maxLen: number;
  exemplo: string;
  mensagem: string;
  placeholder: string;
  mascara: string | null;
};

const MENSAGEM_DEFAULT =
  'Informe um carro válido: C47xxx (Redentor), C30xxx (Futuro) ou D13xxx (Barra). Exemplos: C47654, C30114 ou D13450.';

const DEFAULT_REGRA: FrotaRegra = {
  regex: /^(C47|C30|D13)[0-9]{3}$/i,
  maxLen: 6,
  exemplo: 'C47654',
  mensagem: MENSAGEM_DEFAULT,
  placeholder: 'Ex.: C47654',
  mascara: null,
};

/** Prefixo canônico por descrição de empresa. */
const PREFIXO_POR_EMPRESA: Record<string, string> = {
  redentor: 'C47',
  futuro: 'C30',
  barra: 'D13',
};

let regraAtiva: FrotaRegra = { ...DEFAULT_REGRA };

/** Aplica regra vinda da API (cadastros.frota_regra). */
export function configurarRegraFrota(
  cfg: {
    regex?: string;
    max_len?: number;
    exemplo?: string;
    mensagem?: string;
    placeholder?: string;
    mascara?: string | null;
  } | null | undefined,
): void {
  if (!cfg) {
    regraAtiva = { ...DEFAULT_REGRA };
    return;
  }
  let regex = DEFAULT_REGRA.regex;
  if (cfg.regex) {
    try {
      regex = new RegExp(cfg.regex, 'i');
    } catch {
      regex = DEFAULT_REGRA.regex;
    }
  }
  regraAtiva = {
    regex,
    maxLen: Math.max(1, Math.min(40, Number(cfg.max_len) || DEFAULT_REGRA.maxLen)),
    exemplo: cfg.exemplo || DEFAULT_REGRA.exemplo,
    mensagem: cfg.mensagem || DEFAULT_REGRA.mensagem,
    placeholder: cfg.placeholder || DEFAULT_REGRA.placeholder,
    mascara: cfg.mascara ?? null,
  };
}

export function regraFrotaAtual(): FrotaRegra {
  return regraAtiva;
}

export function chaveEmpresa(descricao: string | null | undefined): string {
  return String(descricao ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '');
}

/** Prefixo obrigatório da empresa (C47 / C30 / D13) ou null se desconhecida. */
export function prefixoFrotaEmpresa(
  empresaDescricao?: string | null,
): string | null {
  const key = chaveEmpresa(empresaDescricao);
  for (const [nome, prefixo] of Object.entries(PREFIXO_POR_EMPRESA)) {
    if (key.includes(nome)) return prefixo;
  }
  return null;
}

/**
 * Normaliza digitação: maiúsculas, só [A-Z0-9], máx. maxLen.
 * Ex.: `c47654` → `C47654`.
 */
export function normalizarFrotaDigitada(raw: string): string {
  return String(raw ?? '')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, regraAtiva.maxLen);
}

export function regraFrotaEmpresa(
  _empresaDescricao?: string | null,
): FrotaRegra {
  return regraAtiva;
}

export function mascaraGuiaFrotaEmpresa(
  _empresaDescricao?: string | null,
): string | null {
  return regraAtiva.mascara;
}

export function placeholderFrotaEmpresa(
  empresaDescricao?: string | null,
): string {
  const p = prefixoFrotaEmpresa(empresaDescricao);
  if (p) return `Ex.: ${p}654`;
  return regraAtiva.placeholder;
}

export function exemploFrotaEmpresa(
  empresaDescricao?: string | null,
): string {
  const p = prefixoFrotaEmpresa(empresaDescricao);
  if (p) return `${p}654`;
  return regraAtiva.exemplo;
}

/** Digitação parcial compatível com a regra (e prefixo da empresa, se houver). */
export function frotaParcialCompativel(
  numeroFrota: string,
  empresaDescricao?: string | null,
): boolean {
  const frota = normalizarFrotaDigitada(numeroFrota);
  if (!frota) return true;
  if (frota.length > regraAtiva.maxLen) return false;

  const prefixoEmp = prefixoFrotaEmpresa(empresaDescricao);
  if (prefixoEmp) {
    // Deve ser prefixo do canônico da empresa
    if (!prefixoEmp.startsWith(frota) && !frota.startsWith(prefixoEmp.slice(0, frota.length))) {
      // Permite se ainda é início válido do prefixo (ex.: "C", "C4", "C47")
      if (!prefixoEmp.startsWith(frota)) return false;
    }
    if (frota.length >= prefixoEmp.length && !frota.startsWith(prefixoEmp)) {
      return false;
    }
    return true;
  }

  // Sem empresa: qualquer início de C47 / C30 / D13
  const canonicos = ['C47', 'C30', 'D13'];
  return canonicos.some(
    (p) => p.startsWith(frota) || frota.startsWith(p.slice(0, Math.min(frota.length, p.length))),
  );
}

/** Valida frota completa (formato canônico). */
export function validarFrota(numeroFrota: string): string | null {
  const frota = normalizarFrotaDigitada(numeroFrota);
  if (!frota) return regraAtiva.mensagem;
  if (frota.length !== regraAtiva.maxLen && frota.length > regraAtiva.maxLen) {
    return regraAtiva.mensagem;
  }
  if (!regraAtiva.regex.test(frota)) return regraAtiva.mensagem;
  return null;
}

/** Valida formato + compatibilidade com a empresa selecionada. */
export function validarFrotaParaEmpresa(
  numeroFrota: string,
  empresaDescricao?: string | null,
): string | null {
  const base = validarFrota(numeroFrota);
  if (base) return base;
  const frota = normalizarFrotaDigitada(numeroFrota);
  const prefixo = prefixoFrotaEmpresa(empresaDescricao);
  if (prefixo && !frota.startsWith(prefixo)) {
    return `Frota incompatível com a empresa. Use prefixo ${prefixo} (ex.: ${prefixo}654).`;
  }
  return null;
}

export function erroFrotaDuranteDigitacao(
  numeroFrota: string,
  empresaDescricao?: string | null,
): string | null {
  const frota = normalizarFrotaDigitada(numeroFrota);
  if (!frota) return null;
  if (!frotaParcialCompativel(frota, empresaDescricao)) {
    const p = prefixoFrotaEmpresa(empresaDescricao);
    if (p) return `Use o prefixo ${p} para esta empresa.`;
    return regraAtiva.mensagem;
  }
  if (frota.length >= regraAtiva.maxLen && !regraAtiva.regex.test(frota)) {
    return regraAtiva.mensagem;
  }
  return null;
}

export function frotaFormatoBasicoOk(frota: string): boolean {
  const t = normalizarFrotaDigitada(frota);
  return regraAtiva.regex.test(t);
}
