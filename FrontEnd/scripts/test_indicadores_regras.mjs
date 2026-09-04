/**
 * Regras Indicadores — Tela 10 (config) + visão operacional + autorização.
 * Run: node scripts/test_indicadores_regras.mjs
 */

const PERFIL_ADMIN = 1;
const PERFIL_DESPACHANTE = 2;
const PERFIL_INSPETOR = 3;

function canAccessConfiguracao(codigoPerfil) {
  return codigoPerfil === PERFIL_ADMIN || codigoPerfil === PERFIL_INSPETOR;
}

/** Simula snapshot + edits + Cancelar (não salva). */
function cancelarDescarta(snapshot, edits) {
  return snapshot.map((i) => ({ ...i }));
}

/** Confirmar envia só vinculados. */
function idsParaSalvar(indicadores) {
  return indicadores.filter((i) => i.vinculado).map((i) => i.id_ind);
}

/** Trocar perfil → lista marcada conforme vínculos do perfil (RF-55). */
function aplicarVinculosAoTrocarPerfil(catalogo, vinculadosIds) {
  const set = new Set(vinculadosIds);
  return catalogo.map((i) => ({
    ...i,
    vinculado: set.has(i.id_ind),
  }));
}

/**
 * Backend RN-08: /me/indicadores usa só codigo_perfil da sessão.
 * Query id_perfil/codigo_perfil é ignorada.
 */
function resolverPerfilSessao(sessao, query) {
  void query?.id_perfil;
  void query?.codigo_perfil;
  return sessao.codigo_perfil;
}

function filtrarPermitidos(todos, vinculos, codigoPerfil) {
  const ids = new Set(
    vinculos.filter((v) => v.codigo_perfil === codigoPerfil).map((v) => v.id_ind),
  );
  return todos.filter((i) => ids.has(i.id_ind));
}

/** Despachante não acessa endpoints de config (require_config_access). */
function podeChamarConfigApi(codigoPerfil) {
  return canAccessConfiguracao(codigoPerfil);
}

let failed = 0;
function assert(name, got, expect) {
  const ok = JSON.stringify(got) === JSON.stringify(expect);
  console.log(`${ok ? 'OK' : 'FAIL'}  ${name}`);
  if (!ok) {
    console.log('     got   ', got);
    console.log('     expect', expect);
    failed += 1;
  }
}

const catalogo = [
  { id_ind: 1, descricao: 'Qtc/M' },
  { id_ind: 2, descricao: 'IPK' },
  { id_ind: 3, descricao: 'KM' },
];

// --- Trocar perfil (RF-55) ---
const marcadosInspetor = aplicarVinculosAoTrocarPerfil(catalogo, [1, 3]);
assert(
  'trocar → Inspetor marca 1 e 3',
  marcadosInspetor.map((i) => i.vinculado),
  [true, false, true],
);
const marcadosDesp = aplicarVinculosAoTrocarPerfil(catalogo, [2]);
assert(
  'trocar → Despachante marca só 2',
  marcadosDesp.map((i) => i.vinculado),
  [false, true, false],
);

// --- Confirmar ---
assert('confirmar envia ids vinculados', idsParaSalvar(marcadosInspetor), [1, 3]);

// --- Cancelar ---
const snapshot = marcadosDesp.map((i) => ({ ...i }));
const edits = snapshot.map((i) =>
  i.id_ind === 1 ? { ...i, vinculado: true } : i,
);
assert(
  'antes cancelar edits divergem',
  edits.map((i) => i.vinculado),
  [true, true, false],
);
assert(
  'cancelar restaura snapshot',
  cancelarDescarta(snapshot, edits).map((i) => i.vinculado),
  [false, true, false],
);

// --- Autorização /me (anti URL) ---
const sessaoDesp = { codigo_perfil: PERFIL_DESPACHANTE };
assert(
  'query id_perfil=1 ignorada',
  resolverPerfilSessao(sessaoDesp, { id_perfil: '1', codigo_perfil: '1' }),
  PERFIL_DESPACHANTE,
);

const vinculos = [
  { id_ind: 1, codigo_perfil: PERFIL_ADMIN },
  { id_ind: 1, codigo_perfil: PERFIL_INSPETOR },
  { id_ind: 2, codigo_perfil: PERFIL_DESPACHANTE },
  { id_ind: 3, codigo_perfil: PERFIL_ADMIN },
];
assert(
  'Despachante só vê autorizados',
  filtrarPermitidos(catalogo, vinculos, PERFIL_DESPACHANTE).map((i) => i.id_ind),
  [2],
);
assert(
  'Admin não vaza via filtro Despachante',
  filtrarPermitidos(catalogo, vinculos, PERFIL_DESPACHANTE).some((i) => i.id_ind === 1),
  false,
);

assert('Despachante NÃO config API', podeChamarConfigApi(PERFIL_DESPACHANTE), false);
assert('Inspetor config API', podeChamarConfigApi(PERFIL_INSPETOR), true);
assert('Admin config API', podeChamarConfigApi(PERFIL_ADMIN), true);

process.exit(failed ? 1 : 0);
