# ----------------------------
# Deus seja Louvado!
# ----------------------------

# Deploy e rollback — RedMapa (Fase 2)

## Princípios

1. Frontend em hospedagem **HTTPS** (CDN/static ou Nginx servindo `FrontEnd/dist`).
2. Backend com **Gunicorn** (nunca `python -m BackEnd.app` / Flask debug em produção).
3. **Proxy reverso** (Nginx/Caddy) termina TLS e encaminha `/api` para Gunicorn em loopback.
4. MariaDB e Oracle **somente rede interna** — sem porta pública na internet.
5. Validar acesso mobile em **4G/5G sem VPN** após DNS/TLS.

---

## Frontend

```bash
cd FrontEnd
npm ci
npm run build
# Artefato: FrontEnd/dist/
```

Variáveis de build (se API em outro host):

```bash
VITE_API_URL=https://api.redmapa.exemplo/api/v1
```

Quando front e API compartilham o mesmo domínio via proxy (`/api` → backend), **não** defina `VITE_API_URL` (usa `/api/v1`).

Publicar `dist/` em storage estático + HTTPS (ou Nginx `root`).

---

## Backend (Gunicorn)

```bash
pip install -r requirements.txt
# Exemplo systemd / processo:
gunicorn -w 4 -b 127.0.0.1:5000 --timeout 60 --access-logfile - --error-logfile - \
  BackEnd.wsgi:app
```

Bind **apenas** `127.0.0.1` se o proxy estiver na mesma máquina.

---

## Proxy reverso (Nginx — esboço)

```nginx
server {
  listen 443 ssl http2;
  server_name app.redmapa.exemplo;

  ssl_certificate     /etc/letsencrypt/live/app.redmapa.exemplo/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/app.redmapa.exemplo/privkey.pem;

  root /var/www/redmapa/FrontEnd/dist;
  index index.html;
  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
  }
}
```

CORS: `REDMAPA_CORS_ORIGINS=https://app.redmapa.exemplo`  
Cookies: `REDMAPA_COOKIE_SECURE=true`, `REDMAPA_COOKIE_SAMESITE=lax`

---

## Domínio, TLS, CORS — checklist

- [ ] DNS A/AAAA apontando para o load balancer / host HTTPS
- [ ] Certificado válido (Let's Encrypt ou corporativo); renovação automática
- [ ] HSTS ativo (API seta quando `REDMAPA_COOKIE_SECURE=true`)
- [ ] CORS lista **somente** o domínio do front (sem `*`)
- [ ] MariaDB `:3306` e Oracle `:1521` **não** publicados na internet
- [ ] Firewall: só 443 (e 80→redirect) públicos
- [ ] Smoke mobile 4G/5G: login, listar MAPAs, vincular motorista, baixa

---

## Migrations

Aplicar scripts idempotentes **antes** de subir a nova release da API, em horário de janela:

```bash
python scripts/aplicar_migrate_ocupacao.py
python scripts/aplicar_migrate_p1.py
# demais migrates documentados em database/schema_migrate_*.sql
```

Nunca `DROP`/recriar banco em produção. Backup lógico **antes** de cada migrate.

---

## Plano de rollback de release

### Aplicação (front + API)

1. Manter artefato anterior versionado (tag git + pasta `releases/YYYYMMDD-HHMM/`).
2. Se falha pós-deploy: apontar Nginx `root` / symlink para o `dist` anterior; reiniciar Gunicorn com o commit/tag anterior.
3. Confirmar `GET /api/v1/health` → `ok: true`.
4. Smoke: login + 1 MAPA + ocupação.

### Banco

1. Dump MariaDB antes de migrate: `mysqldump --single-transaction ... > backup_pre_release.sql`
2. Preferir migrates **aditivos** (colunas/tabelas novas). Se migrate for irreversível, documentar script de compensação **antes** de aplicar.
3. Rollback de schema só com restore do dump (janela de manutenção) — alinhar com negócio (perda de dados pós-migrate).
4. Oracle: nenhuma alteração de schema RedMapa no ERP; falhas Oracle não exigem rollback de DB local além da app.

### Critério de abort

Qualquer P0/P1 falhando em smoke pós-deploy → **rollback imediato** da app; não “deixar para amanhã”.
