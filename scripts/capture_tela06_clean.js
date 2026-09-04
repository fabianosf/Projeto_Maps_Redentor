/**
 * Re-captura limpa da Tela 06 - Cadastro de Mapa (sem toast sobreposto).
 */
const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = 'http://localhost:5173';
const VIEWPORT = { width: 360, height: 800 };
const OUT_DIR  = path.join(__dirname, '..', 'screenshots');
const MAPA_ID  = 2; // mapa existente na base

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx  = await browser.newContext();
  const page = await ctx.newPage();
  await page.setViewportSize(VIEWPORT);

  // Login direto para a principal (usuário 60001 com trocar_senha=0)
  await page.goto(BASE_URL + '/');
  await page.waitForTimeout(1000);
  await page.fill('input[name="matricula"]', '60001');
  await page.fill('input[name="senha"]', '12345');
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('**/principal', { timeout: 15000 });
  console.log('Login OK: ' + page.url());

  // Abre mapa existente em edição (botão REGISTRO visível)
  await page.goto(BASE_URL + `/mapas/${MAPA_ID}`);
  await page.waitForTimeout(2000);
  console.log('Mapa: ' + page.url());

  // Remove qualquer toast/mensagem sobreposta antes da captura
  await page.evaluate(() => {
    document.querySelectorAll('[data-sonner-toaster], [data-sonner-toast], li[data-sonner-toast]')
      .forEach((el) => el.remove());
  });
  await page.waitForTimeout(300);

  const mapaPath = path.join(OUT_DIR, '04_cadastro_mapa.png');
  await page.screenshot({ path: mapaPath, fullPage: false });
  console.log('Capturado: 04_cadastro_mapa.png');

  await ctx.close();
  await browser.close();
  console.log('Concluído.');
})();
