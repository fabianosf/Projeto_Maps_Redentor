/**
 * Captura todas as telas roteadas do RedMapa e gera um PDF.
 * Uso: node scripts/gerar_pdf_telas.mjs
 */
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const require = createRequire(join(ROOT, 'FrontEnd', 'package.json'));
const { chromium } = require('playwright');
const OUT_DIR = join(ROOT, 'docs', 'catalogo-telas');
const SHOTS = join(OUT_DIR, 'screenshots');
const BASE = process.env.REDMAPA_FE_URL || 'http://127.0.0.1:5173';
const API = process.env.REDMAPA_API_URL || 'http://127.0.0.1:5000';

const PUBLIC = [
  { route: '/login', title: 'Login', slug: '01-login' },
  { route: '/recuperar-senha', title: 'Recuperar senha', slug: '02-recuperar-senha' },
  { route: '/primeiro-acesso', title: 'Primeiro acesso', slug: '03-primeiro-acesso' },
];

const AUTHED = [
  { route: '/principal', title: 'Início', slug: '04-inicio' },
  { route: '/mapas', title: 'Mapas — lista', slug: '05-mapas-lista' },
  { route: '/mapas/novo', title: 'Novo mapa', slug: '06-mapa-novo' },
  { route: '/mapas/:id', title: 'Detalhe do mapa', slug: '07-mapa-detalhe', needsMap: true },
  { route: '/mapas/:id/editar', title: 'Editar mapa', slug: '08-mapa-editar', needsMap: true },
  { route: '/guia', title: 'Guia', slug: '09-guia' },
  { route: '/guia/nova', title: 'Nova guia', slug: '10-guia-nova' },
  { route: '/registros', title: 'Registros', slug: '11-registros' },
  { route: '/entrada-saida', title: 'Chegada | Saída', slug: '12-entrada-saida' },
  { route: '/banco-horas', title: 'Banco de horas', slug: '13-banco-horas' },
  { route: '/indicadores', title: 'Indicadores', slug: '14-indicadores' },
  { route: '/mais', title: 'Mais', slug: '15-mais' },
  { route: '/configuracao', title: 'Configuração', slug: '16-configuracao' },
  { route: '/configuracao/indicadores', title: 'Config. indicadores', slug: '17-config-indicadores' },
  { route: '/usuarios', title: 'Cadastro de usuário', slug: '18-usuarios' },
];

mkdirSync(SHOTS, { recursive: true });

async function ensureMapId(page) {
  // Usa o proxy do Vite (mesmo cookie de sessão do browser).
  const list = await page.evaluate(async () => {
    const res = await fetch('/api/v1/mapas', { credentials: 'include' });
    return { status: res.status, data: await res.json().catch(() => ({})) };
  });
  const mapas = list.data?.mapas || list.data?.items || [];
  if (Array.isArray(mapas) && mapas.length) {
    return Number(mapas[0].id_registro);
  }
  const cad = await page.evaluate(async () => {
    const res = await fetch('/api/v1/cadastros', { credentials: 'include' });
    return await res.json().catch(() => ({}));
  });
  const c = cad.cadastros || {};
  const idEmpresa = Number(c.empresas?.[0]?.id_empresa);
  const idTurno = Number(c.turnos?.[0]?.id_turno);
  const created = await page.evaluate(
    async ({ idEmpresa, idTurno }) => {
      const res = await fetch('/api/v1/mapas', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_empresa: idEmpresa,
          id_turno: idTurno,
          codigo_turno: 1,
          turno: 'TURNO 01',
          data: new Date().toISOString().slice(0, 10),
          inicio_jornada_des: '05:00',
          fim_jornada_des: '14:00',
          observacao: 'Catálogo de telas (temporário)',
        }),
      });
      return { status: res.status, data: await res.json().catch(() => ({})) };
    },
    { idEmpresa, idTurno },
  );
  const id = Number(created.data?.mapa?.id_registro);
  if (!Number.isFinite(id) || id <= 0) {
    throw new Error(`Falha ao criar MAPA para screenshots: ${JSON.stringify(created)}`);
  }
  return id;
}

async function shot(page, { route, title, slug }, mapId) {
  const urlPath = route.includes(':id') ? route.replace(':id', String(mapId)) : route;
  const url = `${BASE}${urlPath}`;
  console.log(`→ ${title} (${urlPath})`);
  await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 }).catch(async () => {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  });
  await page.waitForTimeout(800);
  const file = join(SHOTS, `${slug}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return { title, route: urlPath, file, slug };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 430, height: 932 },
    deviceScaleFactor: 2,
    locale: 'pt-BR',
  });
  const page = await context.newPage();
  const catalog = [];

  // Public screens (sem login)
  for (const s of PUBLIC) {
    catalog.push(await shot(page, s, null));
  }

  // Login via UI
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
  await page.getByLabel(/matr[ií]cula/i).fill('59817');
  await page.locator('input[name="senha"], input[type="password"]').first().fill('123');
  await page.getByRole('button', { name: /entrar|acessar|login/i }).click();
  await page.waitForURL(/\/(principal|mais|mapas)/, { timeout: 25000 }).catch(() => {});
  await page.waitForTimeout(1200);

  const mapId = await ensureMapId(page);
  console.log(`MAPA de referência: ${mapId}`);

  for (const s of AUTHED) {
    catalog.push(await shot(page, s, mapId));
  }

  await browser.close();

  const manifest = join(OUT_DIR, 'manifest.json');
  writeFileSync(manifest, JSON.stringify(catalog, null, 2));
  console.log(`Screenshots: ${catalog.length} → ${SHOTS}`);

  const py = join(ROOT, '.venv', 'bin', 'python');
  const builder = join(__dirname, 'montar_pdf_telas.py');
  const r = spawnSync(py, [builder, OUT_DIR], { stdio: 'inherit' });
  if (r.status !== 0) process.exit(r.status || 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
