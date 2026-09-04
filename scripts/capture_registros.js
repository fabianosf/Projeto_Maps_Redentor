/** Re-captura Tela 07 - Registros do Mapa com o novo layout. */
const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT = { width: 360, height: 800 };
const OUT_DIR  = path.join(__dirname, '..', 'screenshots');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx  = await browser.newContext();
  const page = await ctx.newPage();
  await page.setViewportSize(VIEWPORT);

  await page.goto(BASE_URL + '/');
  await page.waitForTimeout(1200);
  await page.fill('input[name="matricula"]', '60001');
  await page.fill('input[name="senha"]', '12345');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(3000);
  console.log('URL após login: ' + page.url());

  await page.goto(BASE_URL + '/mapas/2/registros');
  await page.waitForTimeout(2000);
  const fp = path.join(OUT_DIR, '05_registros.png');
  await page.screenshot({ path: fp, fullPage: false });
  console.log('Capturado: 05_registros.png  [' + page.url() + ']');

  await ctx.close();
  await browser.close();
  console.log('Concluído.');
})();
