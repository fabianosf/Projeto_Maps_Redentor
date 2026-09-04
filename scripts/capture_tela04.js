/** Captura Tela 04 — Principal (RedMapa). */
const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT = { width: 360, height: 800 };
const OUT = path.join(__dirname, '..', 'screenshots', 'mockups', '10_principal.png');

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

  await page.goto(BASE_URL + '/principal');
  await page.waitForTimeout(1500);
  await page.screenshot({
    path: OUT,
    fullPage: false,
  });
  console.log('Capturado: 10_principal.png');

  await ctx.close();
  await browser.close();
})();
