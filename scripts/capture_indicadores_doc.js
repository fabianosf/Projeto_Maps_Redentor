/** Captura Tela 08 — Indicadores (mockup estático para documentação). */
const { chromium } = require('playwright');
const path = require('path');

const VIEWPORT = { width: 360, height: 800 };
const HTML = path.join(__dirname, 'mockups', 'indicadores_doc.html');
const OUT = path.join(__dirname, '..', 'screenshots', 'mockups', '18_indicadores.png');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize(VIEWPORT);
  await page.goto('file:///' + HTML.replace(/\\/g, '/'));
  await page.waitForTimeout(500);
  await page.screenshot({ path: OUT, fullPage: false });
  console.log('Capturado:', OUT);
  await browser.close();
})();
