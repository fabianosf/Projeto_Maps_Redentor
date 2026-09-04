/**
 * Asserts login client-side validation cases (Tela 01).
 * Run: node scripts/test_login_validation.mjs
 */
const isValidMatricula = (value) => /^\d{1,5}$/.test(String(value).trim());
const isValidPasswordFormat = (value) =>
  /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]).{8,}$/.test(
    String(value).trim(),
  );

const cases = [
  { name: 'matricula com letra', value: '12a45', fn: isValidMatricula, expect: false },
  { name: 'matricula 6 digitos', value: '123456', fn: isValidMatricula, expect: false },
  { name: 'matricula valida', value: '59492', fn: isValidMatricula, expect: true },
  { name: 'senha fraca', value: 'senha', fn: isValidPasswordFormat, expect: false },
  { name: 'senha valida Admin', value: 'Admin123!', fn: isValidPasswordFormat, expect: true },
];

let failed = 0;
for (const c of cases) {
  const got = c.fn(c.value);
  const ok = got === c.expect;
  console.log(`${ok ? 'OK' : 'FAIL'}  ${c.name}: ${JSON.stringify(c.value)} => ${got}`);
  if (!ok) failed += 1;
}

process.exit(failed ? 1 : 0);
