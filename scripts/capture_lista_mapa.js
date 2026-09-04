/**
 * Re-captura apenas a Tela 05 - Lista de Mapas com o novo layout.
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT = { width: 360, height: 800 };
const OUT_DIR  = path.join(__dirname, '..', 'screenshots');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx  = await browser.newContext();
  const page = await ctx.newPage();
  await page.setViewportSize(VIEWPORT);

  // Login com 60001 / 12345
  await page.goto(BASE_URL + '/');
  await page.waitForTimeout(1200);
  await page.fill('input[name="matricula"]', '60001');
  await page.fill('input[name="senha"]', '12345');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(3000);
  console.log('URL após login: ' + page.url());

  // Capturar Lista de Mapas
  await page.goto(BASE_URL + '/lista-mapa');
  await page.waitForTimeout(2000);
  const filePath = path.join(OUT_DIR, '03_lista_mapa.png');
  await page.screenshot({ path: filePath, fullPage: false });
  console.log('Capturado: 03_lista_mapa.png  [' + page.url() + ']');

  await ctx.close();
  await browser.close();
  console.log('Concluído.');
})();
