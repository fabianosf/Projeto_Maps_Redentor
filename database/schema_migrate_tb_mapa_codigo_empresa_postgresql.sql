-- Migração PostgreSQL: código sequencial de MAPA por empresa + sequence de cod_map
-- Idempotente. Espelho funcional de schema_migrate_tb_mapa_codigo_empresa.sql
-- Sem blocos DO $$ (aplicador divide por ';').

-- ---------------------------------------------------------------------------
-- 1) Prefixo configurável na empresa
-- ---------------------------------------------------------------------------
ALTER TABLE tb_empresa
    ADD COLUMN IF NOT EXISTS prefixo_mapa VARCHAR(10) NULL;

UPDATE tb_empresa SET prefixo_mapa = 'Red'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao ILIKE '%Redentor%';

UPDATE tb_empresa SET prefixo_mapa = 'Fut'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao ILIKE '%Futuro%';

UPDATE tb_empresa SET prefixo_mapa = 'Bar'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao ILIKE '%Barra%';

-- ---------------------------------------------------------------------------
-- 2) Contador por empresa (codigo_mapa: Fut01, Red01…)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_mapa_seq (
    id_empresa  INT NOT NULL,
    ultimo_seq  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_empresa),
    CONSTRAINT fk_tb_mapa_seq_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)
);

-- ---------------------------------------------------------------------------
-- 3) Colunas no MAPA: id_empresa + codigo_mapa; id_linha legado nullable
-- ---------------------------------------------------------------------------
ALTER TABLE tb_map
    ADD COLUMN IF NOT EXISTS id_empresa INT NULL;

ALTER TABLE tb_map
    ADD COLUMN IF NOT EXISTS codigo_mapa VARCHAR(20) NULL;

ALTER TABLE tb_map
    ALTER COLUMN id_linha DROP NOT NULL;

-- Compatível com consultas de detalhe (JOIN por item.id_linha)
ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS id_linha INT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uk_tb_map_codigo_mapa ON tb_map (codigo_mapa);

CREATE INDEX IF NOT EXISTS idx_tb_map_id_empresa ON tb_map (id_empresa);

-- ---------------------------------------------------------------------------
-- 4) Sequence atômica para cod_map (única global)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS tb_map_cod_map_seq
    AS INTEGER
    INCREMENT BY 1
    MINVALUE 1
    NO CYCLE;

SELECT CASE
    WHEN COALESCE((SELECT MAX(cod_map) FROM tb_map), 0) < 1
        THEN setval('tb_map_cod_map_seq', 1, false)
    ELSE setval(
        'tb_map_cod_map_seq',
        (SELECT MAX(cod_map) FROM tb_map),
        true
    )
END;

-- ---------------------------------------------------------------------------
-- 5) Backfill id_empresa legados + inicializa sequências por empresa
-- ---------------------------------------------------------------------------
UPDATE tb_map m
SET id_empresa = COALESCE(
    m.id_empresa,
    (
        SELECT l_hdr.id_empresa
        FROM tb_linha l_hdr
        WHERE l_hdr.id_linha = m.id_linha
        LIMIT 1
    )
)
WHERE m.id_empresa IS NULL;

INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq)
SELECT e.id_empresa, 0
FROM tb_empresa e
WHERE e.prefixo_mapa IS NOT NULL
  AND TRIM(e.prefixo_mapa) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM tb_mapa_seq s WHERE s.id_empresa = e.id_empresa
  );
