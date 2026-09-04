/**
 * Re-captura Tela 06 (Cadastro de Mapa) e Tela 11 (Configuração) com o novo layout.
 */
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

  // Login com 60001 / 12345
  await page.goto(BASE_URL + '/');
  await page.waitForTimeout(1200);
  await page.fill('input[name="matricula"]', '60001');
  await page.fill('input[name="senha"]', '12345');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(3000);
  console.log('URL após login: ' + page.url());

  // Tela 11 — Configuração (com novo botão Cadastro de Motoristas)
  await page.goto(BASE_URL + '/configuracao');
  await page.waitForTimeout(1500);
  const configPath = path.join(OUT_DIR, '13_configuracao.png');
  await page.screenshot({ path: configPath, fullPage: false });
  console.log('Capturado: 13_configuracao.png  [' + page.url() + ']');

  // Tela 06 — Cadastro de Mapa (com botão REGISTRO na barra de título)
  // Usa o mapa existente de id mais baixo para mostrar a tela preenchida
  await page.goto(BASE_URL + '/lista-mapa');
  await page.waitForTimeout(1500);
  // Clica na primeira linha da tabela para selecionar
  const rows = page.locator('tbody tr');
  const count = await rows.count();
  let mapaId = null;
  if (count > 0) {
    await rows.first().click();
    await page.waitForTimeout(500);
    // Clica no botão de editar (pencil)
    await page.locator('button[aria-label="Editar mapa"]').click();
    await page.waitForTimeout(1500);
    console.log('URL Cadastro de Mapa: ' + page.url());
  } else {
    // Sem mapas: abre tela de novo mapa
    await page.goto(BASE_URL + '/mapas');
    await page.waitForTimeout(1500);
  }
  const mapaPath = path.join(OUT_DIR, '04_cadastro_mapa.png');
  await page.screenshot({ path: mapaPath, fullPage: false });
  console.log('Capturado: 04_cadastro_mapa.png  [' + page.url() + ']');

  await ctx.close();
  await browser.close();
  console.log('Concluído.');
})();
