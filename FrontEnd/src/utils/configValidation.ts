/** Validação local da QTD de tentativas (backend é a fonte da verdade). */
export function validarQtdMaxTentativas(raw: string): string | null {
  const valor = raw.trim();
  if (!valor) {
    return 'Informe a quantidade de tentativas de login.';
  }
  if (!/^\d+$/.test(valor)) {
    return 'Informe um valor numérico para Qtd/T.';
  }
  const qtd = Number(valor);
  if (qtd < 1 || qtd > 9) {
    return 'QTD deve estar entre 1 e 9.';
  }
  return null;
}
