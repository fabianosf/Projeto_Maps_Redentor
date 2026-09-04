/**
 * Playwright script: captura screenshots de todas as telas do RedMapa
 * Samsung Galaxy A03 viewport: 360x800 (device pixel ratio 2)
 *
 * Ordem de apresentação (fluxo da aplicação):
 *  01 Login
 *  02 Cadastro de Senha (1º acesso)
 *  03 Lista de Mapas
 *  04 Cadastro de Mapa
 *  05 Registros do Mapa
 *  06 Cadastro de Registro
 *  07 Viagens
 *  08 Cadastro de Viagem
 *  09 Mapa (visão completa)
 *  10 Principal (RedMapa - hub de navegação)
 *  11 Cadastro de Usuário (edição)
 *  12 Novo Usuário
 *  13 Configuração
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT  = { width: 360, height: 800 };

const OUT_DIR = path.join(__dirname, '..', 'screenshots');
if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

async function screenshot(page, name, label) {
  const filePath = path.join(OUT_DIR, `${name}.png`);
  await page.waitForTimeout(900);
  await page.screenshot({ path: filePath, fullPage: false });
  console.log(`  ✓ ${label} → ${name}.png  [${page.url()}]`);
  return filePath;
}

(async () => {
  const browser = await chromium.launch({ headless: true });

  // ─── Tela 01: Login ───────────────────────────────────────────────────────
  console.log('Capturando telas...\n');
  {
    const ctx  = await browser.newContext();
    const page = await ctx.newPage();
    await page.setViewportSize(VIEWPORT);
    await page.goto(BASE_URL + '/');
    await page.waitForTimeout(1500);
    await screenshot(page, '01_login', 'Tela 01 - Login');
    await ctx.close();
  }

  // ─── Tela 02: Cadastro de Senha (1º acesso — user 60005) ─────────────────
  {
    const ctx  = await browser.newContext();
    const page = await ctx.newPage();
    await page.setViewportSize(VIEWPORT);
    await page.goto(BASE_URL + '/');
    await page.waitForTimeout(1200);
    await page.fill('input[name="matricula"]', '60005');
    await page.fill('input[name="senha"]', '12345');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    console.log(`  [02] URL: ${page.url()}`);
    await screenshot(page, '02_cadastro_senha', 'Tela 02 - Cadastro de Senha');
    await ctx.close();
  }

  // ─── Sessão autenticada (60001 / 12345) ───────────────────────────────────
  const authCtx  = await browser.newContext();
  const authPage = await authCtx.newPage();
  await authPage.setViewportSize(VIEWPORT);

  await authPage.goto(BASE_URL + '/');
  await authPage.waitForTimeout(1200);
  await authPage.fill('input[name="matricula"]', '60001');
  await authPage.fill('input[name="senha"]', '12345');
  await authPage.locator('button[type="submit"]').click();
  await authPage.waitForTimeout(3000);
  console.log(`  [auth] URL após login: ${authPage.url()}`);

  if (!authPage.url().includes('principal') && !authPage.url().includes('lista')) {
    console.log('  [ERRO] Login falhou! Verifique credenciais.');
  }

  // ─── Tela 03: Lista de Mapas ──────────────────────────────────────────────
  await authPage.goto(BASE_URL + '/lista-mapa');
  await authPage.waitForTimeout(2200);
  await screenshot(authPage, '03_lista_mapa', 'Tela 03 - Lista de Mapas');

  // ─── Tela 04: Cadastro de Mapa ────────────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapas/2');
  await authPage.waitForTimeout(1800);
  await screenshot(authPage, '04_cadastro_mapa', 'Tela 04 - Cadastro de Mapa');

  // ─── Tela 05: Registros do Mapa ───────────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapas/2/registros');
  await authPage.waitForTimeout(1800);
  await screenshot(authPage, '05_registros', 'Tela 05 - Registros do Mapa');

  // ─── Tela 06: Cadastro de Registro ───────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapas/2/registros/novo');
  await authPage.waitForTimeout(1500);
  await screenshot(authPage, '06_cadastro_registro', 'Tela 06 - Cadastro de Registro');

  // ─── Tela 07: Viagens ─────────────────────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapas/2/registros/1/viagens');
  await authPage.waitForTimeout(2000);
  await screenshot(authPage, '07_viagens', 'Tela 07 - Viagens');

  // ─── Tela 08: Cadastro de Viagem ─────────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapas/2/registros/1/viagens/novo');
  await authPage.waitForTimeout(1800);
  await screenshot(authPage, '08_cadastro_viagem', 'Tela 08 - Cadastro de Viagem');

  // ─── Tela 09: Mapa (visão completa) ──────────────────────────────────────
  await authPage.goto(BASE_URL + '/mapa/2');
  await authPage.waitForTimeout(2000);
  await screenshot(authPage, '09_mapa', 'Tela 09 - Mapa');

  // ─── Tela 10: Principal (hub de navegação) ────────────────────────────────
  await authPage.goto(BASE_URL + '/principal');
  await authPage.waitForTimeout(1500);
  await screenshot(authPage, '10_principal', 'Tela 10 - Principal (RedMapa)');

  // ─── Tela 11: Cadastro de Usuário (edição) ────────────────────────────────
  await authPage.goto(BASE_URL + '/cadastro-usuario');
  await authPage.waitForTimeout(1500);
  try {
    await authPage.fill('input[name="matricula"]', '60001');
    const btn = authPage.locator('button').filter({ hasText: /pesqui|search/i }).first();
    await btn.click();
    await authPage.waitForTimeout(1200);
  } catch(e) {}
  await screenshot(authPage, '11_usuarios', 'Tela 11 - Cadastro de Usuário');

  // ─── Tela 12: Novo Usuário ────────────────────────────────────────────────
  await authPage.goto(BASE_URL + '/cadastro-usuario');
  await authPage.waitForTimeout(1500);
  try {
    const btns = await authPage.locator('button').all();
    for (const b of btns) {
      const txt = await b.textContent();
      if (txt && (txt.trim() === '+' || txt.toLowerCase().includes('nov'))) {
        await b.click();
        await authPage.waitForTimeout(1000);
        break;
      }
    }
  } catch(e) {}
  await screenshot(authPage, '12_novo_usuario', 'Tela 12 - Novo Usuário');

  // ─── Tela 13: Configuração ────────────────────────────────────────────────
  await authPage.goto(BASE_URL + '/configuracao');
  await authPage.waitForTimeout(1500);
  await screenshot(authPage, '13_configuracao', 'Tela 13 - Configuração');

  await authCtx.close();
  await browser.close();

  console.log('\nConcluído! Screenshots em:', OUT_DIR);
  const files = fs.readdirSync(OUT_DIR).filter(f => f.endsWith('.png'));
  files.forEach(f => console.log(' ', f));
})();
