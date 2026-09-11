/**
 * Validação genérica de frota (independente da empresa).
 * Formato oficial: 47xxx | 30xxx | 13xxx (cinco dígitos).
 * Alinhado a BackEnd/cadastros_service.py — configurável via API (cadastros.frota_regra).
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
  'Informe um carro válido: 47xxx, 30xxx ou 13xxx. Exemplos: 47123, 30123 ou 13123.';

const DEFAULT_REGRA: FrotaRegra = {
  regex: /^(47|30|13)[0-9]{3}$/,
  maxLen: 5,
  exemplo: '47123',
  mensagem: MENSAGEM_DEFAULT,
  placeholder: 'Ex.: 47123',
  mascara: null,
};

const PREFIXOS_PARCIAIS = ['1', '3', '4'] as const;
const PREFIXOS_COMPLETOS = ['13', '30', '47'] as const;

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
      regex = new RegExp(cfg.regex);
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

/** Mantém só dígitos e limita ao tamanho da regra. */
export function normalizarFrotaDigitada(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, regraAtiva.maxLen);
}

/** @deprecated empresa não define mais formato de frota */
export function chaveEmpresa(descricao: string | null | undefined): string {
  return String(descricao ?? '')
    .trim()
    .toLowerCase();
}

/** @deprecated use regraFrotaAtual */
export function regraFrotaEmpresa(
  _empresaDescricao?: string | null,
): FrotaRegra {
  return regraAtiva;
}

/** @deprecated prefixo por empresa removido */
export function prefixoFrotaEmpresa(
  _empresaDescricao?: string | null,
): string | null {
  return null;
}

export function mascaraGuiaFrotaEmpresa(
  _empresaDescricao?: string | null,
): string | null {
  return regraAtiva.mascara;
}

export function placeholderFrotaEmpresa(
  _empresaDescricao?: string | null,
): string {
  return regraAtiva.placeholder;
}

/** @deprecated */
export function exemploFrotaEmpresa(
  _empresaDescricao?: string | null,
): string {
  return regraAtiva.exemplo;
}

export function frotaParcialCompativel(
  numeroFrota: string,
  _empresaDescricao?: string | null,
): boolean {
  const frota = String(numeroFrota ?? '').trim();
  if (!frota) return true;
  if (!/^\d+$/.test(frota)) return false;
  if (frota.length > regraAtiva.maxLen) return false;
  // Regra customizada (API): só exige dígitos até maxLen
  if (regraAtiva.regex.source !== DEFAULT_REGRA.regex.source) {
    return true;
  }
  if (frota.length === 1) {
    return (PREFIXOS_PARCIAIS as readonly string[]).includes(frota);
  }
  return (PREFIXOS_COMPLETOS as readonly string[]).some((p) =>
    frota.startsWith(p),
  );
}

/** Valida frota completa (genérico). */
export function validarFrota(numeroFrota: string): string | null {
  const frota = String(numeroFrota ?? '').trim();
  if (!frota) return regraAtiva.mensagem;
  if (frota.length > regraAtiva.maxLen) {
    return regraAtiva.mensagem;
  }
  if (!regraAtiva.regex.test(frota)) return regraAtiva.mensagem;
  return null;
}

/**
 * Compat: ignora empresa — mesma validação genérica.
 * @deprecated preferir validarFrota
 */
export function validarFrotaParaEmpresa(
  numeroFrota: string,
  _empresaDescricao?: string | null,
): string | null {
  return validarFrota(numeroFrota);
}

export function erroFrotaDuranteDigitacao(
  numeroFrota: string,
  _empresaDescricao?: string | null,
): string | null {
  const frota = String(numeroFrota ?? '').trim();
  if (!frota) return null;
  if (!frotaParcialCompativel(frota)) {
    return regraAtiva.mensagem;
  }
  if (frota.length >= regraAtiva.maxLen && !regraAtiva.regex.test(frota)) {
    return regraAtiva.mensagem;
  }
  return null;
}

export function frotaFormatoBasicoOk(frota: string): boolean {
  const t = String(frota ?? '').trim();
  return regraAtiva.regex.test(t);
}
