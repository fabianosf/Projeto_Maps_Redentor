/**
 * Testes da política de senha (Tela 02).
 * Run: node scripts/test_primeiro_acesso_validation.mjs
 */

function validarPoliticaSenha(senha) {
  const grafico = /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\;/`~]/;
  if (senha.length < 8) return false;
  if (!/[A-Z]/.test(senha)) return false;
  if (!/[A-Za-z]/.test(senha)) return false;
  if (!/\d/.test(senha)) return false;
  if (!grafico.test(senha)) return false;
  return true;
}

function checkIgualdade(a, b) {
  return a === b;
}

const cases = [
  {
    name: 'senhas diferentes',
    run: () => !checkIgualdade('Admin123!', 'Admin123@'),
    expect: true,
  },
  {
    name: 'senha fraca',
    run: () => !validarPoliticaSenha('senha'),
    expect: true,
  },
  {
    name: 'senha sem maiuscula',
    run: () => !validarPoliticaSenha('senha123!'),
    expect: true,
  },
  {
    name: 'senha valida',
    run: () =>
      checkIgualdade('Admin123!', 'Admin123!') && validarPoliticaSenha('Admin123!'),
    expect: true,
  },
];

let failed = 0;
for (const c of cases) {
  const got = c.run();
  const ok = got === c.expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${c.name}`);
  if (!ok) failed += 1;
}

process.exit(failed ? 1 : 0);
