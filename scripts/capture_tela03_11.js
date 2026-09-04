/**
 * Re-captura Tela 03 (Cadastro de Usuário) e Tela 11 (Configuração).
 */
const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT = { width: 360, height: 800 };
const OUT_DIR = path.join(__dirname, '..', 'screenshots');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.setViewportSize(VIEWPORT);

  await page.goto(BASE_URL + '/');
  await page.waitForTimeout(1200);
  await page.fill('input[name="matricula"]', '60001');
  await page.fill('input[name="senha"]', '12345');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(3000);
  console.log('URL após login: ' + page.url());

  await page.goto(BASE_URL + '/configuracao');
  await page.waitForTimeout(1500);
  const configPath = path.join(OUT_DIR, '13_configuracao.png');
  await page.screenshot({ path: configPath, fullPage: false });
  console.log('Capturado: 13_configuracao.png');

  await page.goto(BASE_URL + '/cadastro-usuario');
  await page.waitForTimeout(1500);
  try {
    const novoBtn = page.locator('button').filter({ hasText: /novo/i }).first();
    await novoBtn.click();
    await page.waitForTimeout(1200);
  } catch (e) {
    console.warn('Modo Novo:', e.message);
  }
  const usuariosPath = path.join(OUT_DIR, '11_usuarios.png');
  await page.screenshot({ path: usuariosPath, fullPage: false });
  console.log('Capturado: 11_usuarios.png');

  await ctx.close();
  await browser.close();
  console.log('Concluído.');
})();
