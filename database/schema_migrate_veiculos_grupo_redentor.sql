-- =============================================================================
-- Migration: popular tb_veiculo a partir de veiculos_grupo_redentor.csv
-- SGBD: PostgreSQL (RedMapa) — NÃO EXECUTAR sem validação
--
-- Origem: 30 veículos (10 por empresa)
--
-- Empresa CSV                  → tb_empresa.descricao / codigo_empresa
--   Viação Redentor            → Redentor / 1
--   Transportes Futuro         → Futuro   / 2
--   Transportes Barra          → Barra    / 3
--
-- Prefixo_Veiculo (ex: C47654) → tb_veiculo.numero_frota (identificador UI)
-- Digitos do prefixo           → codigo_veiculo (INT UNIQUE), ex: C47654→47654
-- placa                        → placeholder sintético = Prefixo (UNIQUE NOT NULL)
-- Consorcio                    → sem coluna na tabela; registrado só no comentário
--
-- ATENÇÃO: tb_veiculo NÃO tinha id_empresa — esta migration adiciona a coluna
--           (FK tb_empresa) para filtrar combo por empresa do MAPA (como tb_linha).
-- Upsert por numero_frota (uk_tb_veiculo_numero).
-- =============================================================================

BEGIN;

-- Garantir empresas
INSERT INTO tb_empresa (codigo_empresa, descricao, ativo) VALUES
    (1, 'Redentor', TRUE),
    (2, 'Futuro', TRUE),
    (3, 'Barra', TRUE)
ON CONFLICT (codigo_empresa) DO UPDATE
SET descricao = EXCLUDED.descricao, ativo = TRUE;

-- Vincular veículo à empresa (necessário para combo dependente)
ALTER TABLE tb_veiculo
    ADD COLUMN IF NOT EXISTS id_empresa INT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_tb_veiculo_empresa'
    ) THEN
        ALTER TABLE tb_veiculo
            ADD CONSTRAINT fk_tb_veiculo_empresa
            FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tb_veiculo_id_empresa ON tb_veiculo (id_empresa);

-- Viação Redentor | C47654 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47654,
    'C47654',
    'C47654',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47114 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47114,
    'C47114',
    'C47114',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47025 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47025,
    'C47025',
    'C47025',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47759 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47759,
    'C47759',
    'C47759',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47281 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47281,
    'C47281',
    'C47281',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47250 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47250,
    'C47250',
    'C47250',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47228 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47228,
    'C47228',
    'C47228',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47142 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47142,
    'C47142',
    'C47142',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47754 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47754,
    'C47754',
    'C47754',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Viação Redentor | C47104 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    47104,
    'C47104',
    'C47104',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Redentor'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30346 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30346,
    'C30346',
    'C30346',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30379 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30379,
    'C30379',
    'C30379',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30456 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30456,
    'C30456',
    'C30456',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30279 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30279,
    'C30279',
    'C30279',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30044 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30044,
    'C30044',
    'C30044',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30302 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30302,
    'C30302',
    'C30302',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30216 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30216,
    'C30216',
    'C30216',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30016 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30016,
    'C30016',
    'C30016',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30015 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30015,
    'C30015',
    'C30015',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Futuro | C30047 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    30047,
    'C30047',
    'C30047',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Futuro'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | C13111 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13111,
    'C13111',
    'C13111',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | D13119 | Santa Cruz
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13119,
    'D13119',
    'D13119',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | C13258 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13258,
    'C13258',
    'C13258',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | D13308 | Santa Cruz
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13308,
    'D13308',
    'D13308',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | C13013 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13013,
    'C13013',
    'C13013',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | D13287 | Santa Cruz
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13287,
    'D13287',
    'D13287',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | C13101 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13101,
    'C13101',
    'C13101',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | D13366 | Santa Cruz
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13366,
    'D13366',
    'D13366',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | C13332 | Transcarioca
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13332,
    'C13332',
    'C13332',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Transportes Barra | D13359 | Santa Cruz
INSERT INTO tb_veiculo (
    codigo_veiculo, numero_frota, placa, ativo, id_empresa
)
SELECT
    13359,
    'D13359',
    'D13359',
    TRUE,
    e.id_empresa
FROM tb_empresa e
WHERE e.descricao = 'Barra'
ON CONFLICT (numero_frota) DO UPDATE SET
    codigo_veiculo = EXCLUDED.codigo_veiculo,
    placa = EXCLUDED.placa,
    ativo = TRUE,
    id_empresa = EXCLUDED.id_empresa;

-- Exigir empresa após o seed
ALTER TABLE tb_veiculo
    ALTER COLUMN id_empresa SET NOT NULL;

-- Conferência
SELECT e.descricao AS empresa, COUNT(*) AS qtd
FROM tb_veiculo v
JOIN tb_empresa e ON e.id_empresa = v.id_empresa
GROUP BY e.descricao
ORDER BY e.descricao;

SELECT numero_frota, codigo_veiculo, placa, e.descricao AS empresa
FROM tb_veiculo v
JOIN tb_empresa e ON e.id_empresa = v.id_empresa
ORDER BY e.codigo_empresa, v.numero_frota
LIMIT 15;

COMMIT;
