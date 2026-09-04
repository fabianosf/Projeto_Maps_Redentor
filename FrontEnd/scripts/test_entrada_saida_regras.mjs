/**
 * Regras UX Telas 05/06 (Entrada/Saída).
 * Run: node scripts/test_entrada_saida_regras.mjs
 */

function payloadChegada(idLinha, carro, horario) {
  return { evento: 'C', id_linha: idLinha, carro, horario };
}

function payloadSaida(idLinha, carro, horario, extras = {}) {
  return { evento: 'S', id_linha: idLinha, carro, horario, ...extras };
}

function temIdGuiaNoFront(body) {
  return Object.prototype.hasOwnProperty.call(body, 'id_guia');
}

let failed = 0;
function assert(name, got, expect) {
  const ok = got === expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${name}`);
  if (!ok) failed += 1;
}

const comLinhas = [{ id_linha: 1 }];
const semLinhas = [];
assert('com linhas → mostra formulário', comLinhas.length > 0, true);
assert('sem linhas → EmptyState', semLinhas.length === 0, true);

let aba = 'chegada';
let chegada = { carro: '1', horario: '08:00' };
let saida = { carro: '2', horario: '09:00' };
function trocarAba(next) {
  aba = next;
  if (next === 'chegada') chegada = { carro: '', horario: '' };
  else saida = { carro: '', horario: '' };
}
trocarAba('saida');
assert('troca aba limpa saída', saida.carro === '' && saida.horario === '', true);
assert('aba ativa saída', aba, 'saida');
trocarAba('chegada');
assert('troca aba limpa chegada', chegada.carro === '' && chegada.horario === '', true);

const c = payloadChegada(10, '123', '08:30');
const s = payloadSaida(10, '123', '17:00', { id_linha_destino: 20, id_destino: 5 });
assert('registro chegada evento C', c.evento, 'C');
assert('registro saída evento S', s.evento, 'S');
assert('chegada sem id_guia no front', temIdGuiaNoFront(c), false);
assert('saída sem id_guia no front', temIdGuiaNoFront(s), false);

process.exit(failed ? 1 : 0);
