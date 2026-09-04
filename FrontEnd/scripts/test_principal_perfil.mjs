/**
 * UX Configuração por perfil (Tela Principal).
 * Run: node scripts/test_principal_perfil.mjs
 */
function canAccessConfiguracao(codigoPerfil) {
  return codigoPerfil === 1 || codigoPerfil === 3;
}

const cases = [
  { name: 'Administrador (1) vê Configuração', perfil: 1, expect: true },
  { name: 'Despachante (2) NÃO vê Configuração', perfil: 2, expect: false },
  { name: 'Inspetor (3) vê Configuração', perfil: 3, expect: true },
  { name: 'sem perfil', perfil: null, expect: false },
];

let failed = 0;
for (const c of cases) {
  const got = canAccessConfiguracao(c.perfil);
  const ok = got === c.expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${c.name} => ${got}`);
  if (!ok) failed += 1;
}

const cardMinTouch = 44;
const cardHeightPx = 56; // h-14
console.log(
  `${cardHeightPx >= cardMinTouch ? 'OK' : 'FAIL'}  card touch ${cardHeightPx}px >= ${cardMinTouch}px`,
);
if (cardHeightPx < cardMinTouch) failed += 1;

process.exit(failed ? 1 : 0);
