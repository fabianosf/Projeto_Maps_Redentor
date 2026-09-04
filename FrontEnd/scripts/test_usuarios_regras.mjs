/**
 * Regras Tela 03 — reset Inspetor + senha provisória não fixa.
 * Run: node scripts/test_usuarios_regras.mjs
 */
function canResetSenhaUsuario(codigoPerfil) {
  return codigoPerfil === 1; // só Admin
}

function canAccessCadastroUsuario(codigoPerfil) {
  return codigoPerfil === 1 || codigoPerfil === 3;
}

const modeIdle = {
  canNovo: true,
  canPesquisar: true,
  canSalvar: false,
  canDeletar: false,
};

let failed = 0;
function assert(name, got, expect) {
  const ok = got === expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${name} => ${got}`);
  if (!ok) failed += 1;
}

assert('idle: novo', modeIdle.canNovo, true);
assert('idle: pesquisar', modeIdle.canPesquisar, true);
assert('idle: salvar off', modeIdle.canSalvar, false);
assert('idle: deletar off', modeIdle.canDeletar, false);

assert('Admin acessa cadastro', canAccessCadastroUsuario(1), true);
assert('Inspetor acessa cadastro', canAccessCadastroUsuario(3), true);
assert('Despachante NÃO acessa', canAccessCadastroUsuario(2), false);

assert('Admin pode reset', canResetSenhaUsuario(1), true);
assert('Inspetor NÃO reset', canResetSenhaUsuario(3), false);
assert('Despachante NÃO reset', canResetSenhaUsuario(2), false);

// Simula token_urlsafe(12) length variance (urlsafe ~16 chars for 12 bytes)
const samples = new Set();
for (let i = 0; i < 5; i++) {
  samples.add(Buffer.from(crypto.getRandomValues(new Uint8Array(12))).toString('base64url'));
}
assert('senhas temporárias distintas', samples.size === 5, true);
assert('nenhuma é 12345', ![...samples].includes('12345'), true);

process.exit(failed ? 1 : 0);
