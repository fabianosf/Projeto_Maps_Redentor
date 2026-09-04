# Tutorial — Testar o RedMapa no celular (Windows + ngrok)

> **Termo correto:** **ngrok** (não “grok”). É um túnel que expõe o servidor da sua máquina na internet, para o celular acessar sem instalar nada além do navegador.

---

## 1. A aplicação está pronta para teste no celular?

### FrontEnd — **Sim**

| Item | Status |
|------|--------|
| Layout mobile-first (`viewport`, `dvh`, botões touch ≥ 44px) | OK |
| `npm run dev` com `--host` (aceita conexões da rede) | OK |
| Vite com `allowedHosts: true` (aceita domínio ngrok) | OK |
| Proxy `/api` → BackEnd local na porta 5000 | OK |

### BackEnd — **Sim**

| Item | Status |
|------|--------|
| Flask escuta em `0.0.0.0:5000` (acessível na rede local) | OK |
| Endpoint de saúde: `GET /api/v1/health` | OK |
| Cookies de sessão (`HttpOnly`, `SameSite=Lax`) compatíveis com teste via proxy | OK |

### Base de dados — **Depende do seu PC**

| Item | Status |
|------|--------|
| Arquivo `DAL/arquivos_crip/arq/map.dat` (config criptografada — **não vai para o Git**) | Você precisa tê-lo localmente |
| Rede/VPN até o servidor MariaDB | O PC deve alcançar o banco (ex.: `10.1.1.29`) |
| Tabelas RedMapa (`tb_usuario`, `tb_guia`, etc.) | Devem existir no banco configurado em `map.dat` |

**Como validar no Windows (PowerShell), na pasta do projeto:**

```powershell
cd "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP"
py -3 scripts/test_db_conexao.py
```

Se aparecer `OK — conexão estabelecida` e contagem de usuários, o banco está pronto.

**Teste rápido da API (com BackEnd rodando):**

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/v1/health
```

Resposta esperada: `{ "ok": true, "servico": "redmapa-api" }`

---

## 2. Duas formas de testar no celular

| Método | Quando usar |
|--------|-------------|
| **A — Mesma Wi‑Fi (sem ngrok)** | Celular e PC na mesma rede; mais simples |
| **B — ngrok** | Celular em 4G/5G ou outra rede; URL pública temporária |

> **Recomendado para começar:** método **A** (Wi‑Fi). Use **ngrok** se o celular não estiver na mesma rede.

---

## 3. Preparar o PC (uma vez)

### 3.1 Pré-requisitos

- Node.js (para o FrontEnd)
- Python 3 (para o BackEnd)
- Arquivo `map.dat` em `DAL\arquivos_crip\arq\`
- VPN/rede corporativa, se o MariaDB exigir

### 3.2 Instalar o ngrok (só para o método B)

1. Acesse [https://ngrok.com](https://ngrok.com) e crie uma conta gratuita.
2. Baixe o ngrok para Windows e extraia (ex.: `C:\Tools\ngrok\ngrok.exe`).
3. No painel ngrok, copie o **Authtoken** e execute **uma vez**:

```powershell
ngrok config add-authtoken SEU_TOKEN_AQUI
```

---

## 4. Subir a aplicação no PC

Abra **dois terminais** PowerShell.

### Terminal 1 — BackEnd

```powershell
cd "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP"

# Use map.dat (padrão). Se você usa outro .dat:
# $env:REDMAPA_CONFIG = "map"

py -3 -m BackEnd.app
```

Aguarde algo como: `Running on http://0.0.0.0:5000`

### Terminal 2 — FrontEnd

```powershell
cd "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP\FrontEnd"
npm run dev
```

Aguarde: `Local: http://localhost:5173/` e `Network: http://192.168.x.x:5173/`

**Confirme no PC:** abra [http://localhost:5173](http://localhost:5173) e faça login.

---

## 5. Método A — Celular na mesma Wi‑Fi (sem ngrok)

1. No PC, descubra o IP local:

```powershell
ipconfig
```

Procure **Endereço IPv4** da placa Wi‑Fi/Ethernet (ex.: `192.168.1.105`).

2. No celular (mesma Wi‑Fi), abra o navegador:

```
http://192.168.1.105:5173
```

(substitua pelo seu IPv4)

3. Se não carregar, libere a porta no **Firewall do Windows**:

   - Painel → Firewall → Configurações avançadas → Regras de entrada → Nova regra
   - Porta **TCP 5173** (e, se testar API direto, **5000** — normalmente não é necessário porque o Vite faz proxy)

---

## 6. Método B — ngrok (celular em qualquer rede)

### Por que um túnel só?

O FrontEnd em modo dev envia as chamadas `/api/...` para o Flask **via proxy do Vite**. Basta expor a porta **5173**; o celular não precisa acessar a 5000 diretamente.

### Passos

1. BackEnd e FrontEnd já rodando (seção 4).
2. Abra um **terceiro terminal**:

```powershell
ngrok http 5173
```

3. Copie a URL **HTTPS** exibida (ex.: `https://abc123.ngrok-free.app`).
4. No celular, abra essa URL no Chrome/Safari.

### Página de aviso do ngrok (plano gratuito)

Na primeira visita pode aparecer “Visit Site”. Toque em **Visit Site** para continuar.

### Credenciais de teste (banco `map` atual)

A senha precisa obedecer **RF-03** (mín. 8 caracteres, maiúscula, dígito e especial).  
`12345` **não passa** nessa validação — o app exibe *Senha inválida!* antes mesmo de consultar o banco.

| Matrícula | Senha | Perfil |
|-----------|-------|--------|
| `59492` | `Admin_2026` | Administrador |
| `59817` | `Admin_2026` | Despachante |

> Os usuários `1001`/`1002` do seed antigo **não existem** neste banco. Use as matrículas acima ou cadastre um usuário na Tela 03.

---

## 7. O que testar no celular

1. **Login** — matrícula, senha, mensagens de erro.
2. **Tela Principal** — botões Configuração, Oficina, Chegada|Saída, Guia.
3. **Cancelar (RF-05)** — em mobile prioriza `history.back()`; sessão é encerrada mesmo se a aba não fechar.
4. **Rotação / teclado** — campos numéricos e formulários longos (Guia, Mensagem).
5. **Perfis** — Despachante não vê Configuração; Inspetor sem Reset na Tela 03.

---

## 8. Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Tela carrega, login falha “serviço indisponível” | BackEnd parado ou banco inacessível | Terminal 1 rodando; `test_db_conexao.py`; VPN |
| `map.dat não encontrado` | Config ausente | Copiar `map.dat` para `DAL\arquivos_crip\arq\` |
| Celular não abre IP local | Redes diferentes ou firewall | Mesma Wi‑Fi; regra firewall 5173 |
| ngrok abre, API falha | Só FrontEnd rodando | Subir BackEnd na porta 5000 |
| ngrok: “Blocked host” | Host não permitido | Já corrigido no projeto (`allowedHosts: true`) |
| Login OK no PC, falha no celular via ngrok | Cookie/sessão | Use **um** túnel na 5173 (não dois túneis separados) |
| URL ngrok muda toda vez | Plano gratuito | Normal; copie a nova URL a cada sessão |

---

## 9. Encerrar o teste

1. `Ctrl+C` no ngrok (se usou).
2. `Ctrl+C` no FrontEnd e no BackEnd.
3. Feche a aba no celular.

---

## 10. Resumo do fluxo (ngrok)

```
[Celular]  --HTTPS-->  [ngrok na nuvem]  -->  [PC: Vite :5173]
                                              |
                                              +--> proxy /api
                                                   [PC: Flask :5000]
                                                        |
                                                        [MariaDB via map.dat]
```

---

## Referências no projeto

- FrontEnd dev: `FrontEnd/package.json` → `"dev": "vite --host --port 5173"`
- Proxy API: `FrontEnd/vite.config.ts`
- BackEnd: `py -3 -m BackEnd.app` (`REDMAPA_HOST=0.0.0.0`, porta 5000)
- Teste DB: `scripts/test_db_conexao.py`
