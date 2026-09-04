/**
 * Validações locais Tela 08 (Guia).
 * Run: node scripts/test_guia_validation.mjs
 */
function isValidHHMM(value) {
  if (!/^\d{2}:\d{2}$/.test(value)) return false;
  const h = Number(value.slice(0, 2));
  const m = Number(value.slice(3, 5));
  return h >= 0 && h <= 23 && m >= 0 && m <= 59;
}

function parseDateBR(value) {
  const m = String(value).trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const dd = Number(m[1]);
  const mm = Number(m[2]);
  const yyyy = Number(m[3]);
  const dt = new Date(yyyy, mm - 1, dd);
  if (dt.getFullYear() !== yyyy || dt.getMonth() !== mm - 1 || dt.getDate() !== dd) {
    return null;
  }
  return `${m[1]}/${m[2]}/${m[3]}`;
}

function validar(payload) {
  if (!payload.numero.trim()) return 'Informe o NR(Guia).';
  if (!parseDateBR(payload.data.trim())) return 'Data inválida.';
  if (payload.horario_pegada && !isValidHHMM(payload.horario_pegada)) {
    return 'INÍCIO(JORNADA) inválido.';
  }
  if (payload.horario_largada && !isValidHHMM(payload.horario_largada)) {
    return 'FIM(JORNADA) inválido.';
  }
  return null;
}

const hoje = (() => {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
})();

let failed = 0;
function assert(name, got, expect) {
  const ok = got === expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${name}`);
  if (!ok) failed += 1;
}

assert(
  'novo válido',
  validar({
    numero: '10001',
    data: hoje,
    horario_pegada: '08:30',
    horario_largada: '17:00',
    carro: '123',
    motorista: '59492',
  }),
  null,
);

assert(
  'horário inválido 25:00',
  validar({
    numero: '10001',
    data: hoje,
    horario_pegada: '25:00',
    horario_largada: '',
  }),
  'INÍCIO(JORNADA) inválido.',
);

assert(
  'horário incompleto 8:3',
  validar({
    numero: '10001',
    data: hoje,
    horario_pegada: '8:3',
    horario_largada: '',
  }),
  'INÍCIO(JORNADA) inválido.',
);

const idle = { salvar: false, deletar: false, novo: true, pesquisar: true };
const include = { salvar: true, deletar: false, novo: true, pesquisar: true };
const edit = { salvar: true, deletar: true, novo: true, pesquisar: true };
assert('idle: só novo/pesquisar p/ ações de edição', idle.salvar || idle.deletar, false);
assert('include: salvar on / deletar off', include.salvar && !include.deletar, true);
assert('edit: salvar+deletar', edit.salvar && edit.deletar, true);

process.exit(failed ? 1 : 0);
