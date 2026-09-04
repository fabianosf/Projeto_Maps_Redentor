/** Captura Tela 02 — Cadastro de Senha (mockup estático para documentação). */
const { chromium } = require('playwright');
const path = require('path');

const VIEWPORT = { width: 360, height: 800 };
const HTML = path.join(__dirname, 'mockups', 'cadastro_senha_doc.html');
const OUT = path.join(__dirname, '..', 'screenshots', 'mockups', '02_cadastro_senha.png');

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
