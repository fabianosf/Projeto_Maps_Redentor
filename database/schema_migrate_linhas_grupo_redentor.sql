-- =============================================================================
-- Migration: popular tb_linha a partir de linhas_grupo_redentor.csv
-- SGBD: PostgreSQL (RedMapa) — NÃO EXECUTAR sem validação
--
-- Regra escolhida: 1 registro por variante de Numero_Linha (separador "/")
-- Origem: 51 linhas CSV → 74 registros em tb_linha
--
-- Empresa CSV                  → tb_empresa.descricao / codigo_empresa
--   Viação Redentor            → Redentor / 1
--   Transportes Futuro         → Futuro   / 2
--   Transportes Barra          → Barra    / 3
--
-- codigo_linha (INT, UNIQUE):
--   número puro .............. 319
--   prefixo SV/SN/SP/SR ...... base*100 + (SV=1,SN=2,SP=3,SR=4)
--                              SV319→31901  SN319→31902  SP343→34303  394SR→39404
--   "558 (INT6)" ............. ignora "(INT6)" → 558
--   descricao ................ variante alfanumérica + itinerário [região]
--
-- id_local_origem/destino: locais padrão codigo 10 e 20 (criados se faltarem).
-- Upsert por codigo_linha (uk_tb_linha_codigo).
-- =============================================================================

BEGIN;

-- Garantir empresas (nomes curtos já usados no app)
INSERT INTO tb_empresa (codigo_empresa, descricao, ativo) VALUES
    (1, 'Redentor', TRUE),
    (2, 'Futuro', TRUE),
    (3, 'Barra', TRUE)
ON CONFLICT (codigo_empresa) DO UPDATE
SET descricao = EXCLUDED.descricao, ativo = TRUE;

-- Locais para FK
INSERT INTO tb_local (codigo_local, descricao, ativo)
SELECT v.codigo_local, v.descricao, TRUE
FROM (VALUES (10, 'Local 10'), (20, 'Local 20')) AS v(codigo_local, descricao)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_local t WHERE t.codigo_local = v.codigo_local
);

-- Linhas
INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    379,
    e.id_empresa,
    'Catiri x Tiradentes [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    383,
    e.id_empresa,
    'Realengo x Praça da República [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    389,
    e.id_empresa,
    'Vila Aliança x Candelária [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    394,
    e.id_empresa,
    'Vila Kennedy x Tiradentes [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    395,
    e.id_empresa,
    'Coqueiros x Tiradentes [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    731,
    e.id_empresa,
    'Ligações em Marechal Hermes e Campo Grande [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    737,
    e.id_empresa,
    'Ligações em Marechal Hermes e Campo Grande [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    739,
    e.id_empresa,
    'Ligações em Marechal Hermes e Campo Grande [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    745,
    e.id_empresa,
    'Bangu / Jabour x Cascadura [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    746,
    e.id_empresa,
    'Bangu / Jabour x Cascadura [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    752,
    e.id_empresa,
    'Jardim Palmares x Coelho Neto [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    756,
    e.id_empresa,
    'Jardim Palmares x Coelho Neto [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    777,
    e.id_empresa,
    'Padre Miguel x Madureira [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    784,
    e.id_empresa,
    'Vila Kennedy x Marechal Hermes [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    790,
    e.id_empresa,
    'Campo Grande x Cascadura [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    794,
    e.id_empresa,
    'Bangu x Cascadura [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    801,
    e.id_empresa,
    'Bangu Shopping, Senador Camará, Sulacap x Taquara [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    803,
    e.id_empresa,
    'Bangu Shopping, Senador Camará, Sulacap x Taquara [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    811,
    e.id_empresa,
    'Bangu / Carobinha [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    812,
    e.id_empresa,
    'Bangu / Carobinha [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    875,
    e.id_empresa,
    'Tanque x Praça Seca [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    878,
    e.id_empresa,
    'Tanque x Barra da Tijuca [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    926,
    e.id_empresa,
    'Senador Camará x Penha [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    936,
    e.id_empresa,
    'Campo Grande x Fundão [Ilha do Fundão / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    39404,
    e.id_empresa,
    '394SR — Vila Kennedy x Tiradentes [Centro / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    77701,
    e.id_empresa,
    'SV777 — Padre Miguel x Madureira [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    79001,
    e.id_empresa,
    'SV790 — Campo Grande x Cascadura [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    80303,
    e.id_empresa,
    'SP803 — Bangu Shopping, Senador Camará, Sulacap x Taquara [Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    343,
    e.id_empresa,
    'Jardim Oceânico / Rio das Pedras x Candelária [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    550,
    e.id_empresa,
    'Cidade de Deus / Rio das Pedras x Gávea [Zona Sul / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    557,
    e.id_empresa,
    'Rio das Pedras x Copacabana [Zona Sul / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    558,
    e.id_empresa,
    'Cidade de Deus x Copacabana [Zona Sul / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    565,
    e.id_empresa,
    'Tanque x Gávea (via Alvorada) [Zona Sul / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    766,
    e.id_empresa,
    'Madureira Shopping x Freguesia (via Cascadura) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    831,
    e.id_empresa,
    'Taquara x Colônia [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    859,
    e.id_empresa,
    'Covanca x Geremário [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    900,
    e.id_empresa,
    'Merck x Downtown (via Alvorada) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    932,
    e.id_empresa,
    'Gardênia Azul x Tanque (via Pau-Ferro) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    953,
    e.id_empresa,
    'Tanque x Cidade de Deus (via Retiro dos Artistas) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    954,
    e.id_empresa,
    'Taquara x Recreio (via Benvindo de Novaes) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    34303,
    e.id_empresa,
    'SP343 — Jardim Oceânico / Rio das Pedras x Candelária [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    306,
    e.id_empresa,
    'Praça Seca x Castelo (via Serra / Pau-Ferro) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    319,
    e.id_empresa,
    'Terminal Alvorada x Central / Terminal Gentileza [Centro / Zona Norte]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    348,
    e.id_empresa,
    'Riocentro x Candelária (via Linha Amarela / Cidade de Deus) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    352,
    e.id_empresa,
    'Riocentro x Candelária (via Parque Olímpico / Linha Amarela) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    353,
    e.id_empresa,
    'Gardênia Azul x Terminal Gentileza (via Méier / Vila Isabel) [Centro / Zona Norte]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    361,
    e.id_empresa,
    'Recreio x Castelo (via Linha Amarela) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    368,
    e.id_empresa,
    'Riocentro x Candelária (via Serra / Gardênia Azul) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    390,
    e.id_empresa,
    'Curicica x Candelária (via Serra / Freguesia) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    552,
    e.id_empresa,
    'Alvorada x Rio Sul / Metrô Botafogo (via Praia da Barra / Av. Niemeyer) [Zona Sul]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    553,
    e.id_empresa,
    'Recreio x Rio Sul (via Alvorada / Av. das Américas) [Zona Sul]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    554,
    e.id_empresa,
    'Piabas x Rio Sul / Metrô Botafogo (via Alvorada / Vargem Grande) [Zona Sul]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    600,
    e.id_empresa,
    'Taquara-Boiúna x Saens Peña [Grande Tijuca / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    601,
    e.id_empresa,
    'Taquara-Capela x Saens Peña (via Grajaú) [Grande Tijuca / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    607,
    e.id_empresa,
    'Cascadura x Rio Comprido [Zona Norte / Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    610,
    e.id_empresa,
    'Tanque x Del Castilho (via Linha Amarela) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    611,
    e.id_empresa,
    'Riocentro x Del Castilho [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    613,
    e.id_empresa,
    'Vargem Grande x Del Castilho (via Linha Amarela) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    614,
    e.id_empresa,
    'Alvorada x Del Castilho (via Linha Amarela) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    636,
    e.id_empresa,
    'Merck x Saens Peña [Grande Tijuca / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    692,
    e.id_empresa,
    'Méier x Alvorada (via Linha Amarela) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    844,
    e.id_empresa,
    'Linhas locais e alimentadoras (Barra / Recreio / Jacarepaguá) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    861,
    e.id_empresa,
    'Linhas locais e alimentadoras (Barra / Recreio / Jacarepaguá) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    862,
    e.id_empresa,
    'Linhas locais e alimentadoras (Barra / Recreio / Jacarepaguá) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    880,
    e.id_empresa,
    'Linhas locais e alimentadoras (Barra / Recreio / Jacarepaguá) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    899,
    e.id_empresa,
    'Linhas locais e alimentadoras (Barra / Recreio / Jacarepaguá) [Local / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    31901,
    e.id_empresa,
    'SV319 — Terminal Alvorada x Central / Terminal Gentileza [Centro / Zona Norte]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    31902,
    e.id_empresa,
    'SN319 — Terminal Alvorada x Central / Terminal Gentileza [Centro / Zona Norte]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    36802,
    e.id_empresa,
    'SN368 — Riocentro x Candelária (via Serra / Gardênia Azul) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    39001,
    e.id_empresa,
    'SV390 — Curicica x Candelária (via Serra / Freguesia) [Centro]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    55202,
    e.id_empresa,
    'SN552 — Alvorada x Rio Sul / Metrô Botafogo (via Praia da Barra / Av. Niemeyer) [Zona Sul]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    55402,
    e.id_empresa,
    'SN554 — Piabas x Rio Sul / Metrô Botafogo (via Alvorada / Vargem Grande) [Zona Sul]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    60002,
    e.id_empresa,
    'SN600 — Taquara-Boiúna x Saens Peña [Grande Tijuca / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

INSERT INTO tb_linha (
    codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
)
SELECT
    69201,
    e.id_empresa,
    'SV692 — Méier x Alvorada (via Linha Amarela) [Zona Norte / Zona Oeste]',
    (SELECT id_local FROM tb_local WHERE codigo_local = 10 LIMIT 1),
    (SELECT id_local FROM tb_local WHERE codigo_local = 20 LIMIT 1),
    TRUE
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (codigo_linha) DO UPDATE SET
    id_empresa = EXCLUDED.id_empresa,
    descricao = EXCLUDED.descricao,
    id_local_origem = EXCLUDED.id_local_origem,
    id_local_destino = EXCLUDED.id_local_destino,
    ativo = TRUE;

-- Conferência
SELECT e.descricao AS empresa, COUNT(*) AS qtd
FROM tb_linha l
JOIN tb_empresa e ON e.id_empresa = l.id_empresa
GROUP BY e.descricao
ORDER BY e.descricao;

COMMIT;
