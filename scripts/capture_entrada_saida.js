/** Captura Tela 12 — Entrada | Saída (com linha selecionada e abas). */
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
  await page.waitForTimeout(3500);
  console.log('URL após login:', page.url());

  if (!page.url().includes('principal') && !page.url().includes('cadastro-senha')) {
    console.log('Login pode ter falhado — tentando continuar mesmo assim');
  }

  await page.goto(BASE_URL + '/entrada-saida');
  await page.waitForTimeout(2500);
  console.log('URL entrada-saida:', page.url());

  try {
    const trigger = page.locator('button').filter({ hasText: /selecione|linha|local/i }).first();
    if (await trigger.count()) {
      await trigger.click({ timeout: 5000 });
      await page.waitForTimeout(600);
      const opt = page.locator('[role="option"]').first();
      if (await opt.count()) {
        await opt.click();
        await page.waitForTimeout(1000);
      }
    }
  } catch (e) {
    console.warn('Seleção de linha:', e.message);
  }

  await page.screenshot({
    path: path.join(OUT_DIR, '14_entrada_saida.png'),
    fullPage: false,
  });
  console.log('Capturado: 14_entrada_saida.png');

  await ctx.close();
  await browser.close();
})();
