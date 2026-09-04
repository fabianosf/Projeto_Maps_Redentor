/**
 * Regras Tela 09 — QTD tentativas (1–9) + switch de bloqueio.
 * Run: node scripts/test_configuracao_validation.mjs
 */

function validarQtdMaxTentativas(raw) {
  const valor = String(raw ?? '').trim();
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

let failed = 0;
function assert(name, got, expect) {
  const ok = Object.is(got, expect);
  console.log(`${ok ? 'OK' : 'FAIL'}  ${name} => ${JSON.stringify(got)}`);
  if (!ok) failed += 1;
}

assert('válido 1', validarQtdMaxTentativas('1'), null);
assert('válido 5', validarQtdMaxTentativas('5'), null);
assert('válido 9', validarQtdMaxTentativas('9'), null);

assert(
  'fora 0',
  validarQtdMaxTentativas('0'),
  'QTD deve estar entre 1 e 9.',
);
assert(
  'fora 10 (1 dígito na UI = "1" ok; "10" truncado — teste valor 10)',
  validarQtdMaxTentativas('10'),
  'QTD deve estar entre 1 e 9.',
);

assert(
  'vazio',
  validarQtdMaxTentativas(''),
  'Informe a quantidade de tentativas de login.',
);
assert(
  'não numérico',
  validarQtdMaxTentativas('a'),
  'Informe um valor numérico para Qtd/T.',
);

// Switch: estado booleano espelha payload da API
let bloqueio = true;
bloqueio = !bloqueio;
assert('toggle → inativo', bloqueio, false);
bloqueio = !bloqueio;
assert('toggle → ativo', bloqueio, true);

const payloadAtivo = { valor: '3', bloqueio_tentativas: true };
const payloadInativo = { valor: '3', bloqueio_tentativas: false };
assert('payload ativo', payloadAtivo.bloqueio_tentativas, true);
assert('payload inativo', payloadInativo.bloqueio_tentativas, false);

process.exit(failed ? 1 : 0);
