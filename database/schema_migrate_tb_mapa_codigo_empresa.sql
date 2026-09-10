-- Migração: código sequencial de MAPA por empresa (ex.: Red01, Fut01, Bar01)
-- Prefixo configurável em tb_empresa.prefixo_mapa; contador em tb_mapa_seq
-- (não reutiliza sequência após exclusão). codigo_mapa UNIQUE em tb_map.
-- Compatível com MariaDB 10.2+.
USE map;

-- ---------------------------------------------------------------------------
-- 1) Prefixo configurável na empresa
-- ---------------------------------------------------------------------------
SET @col_prefixo := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_empresa'
      AND COLUMN_NAME = 'prefixo_mapa'
);

SET @sql := IF(
    @col_prefixo = 0,
    'ALTER TABLE tb_empresa ADD COLUMN prefixo_mapa VARCHAR(10) NULL COMMENT ''Prefixo do código de MAPA (ex.: Red, Fut, Bar)'' AFTER descricao',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Seeds de configuração (dados mestres — não hardcode na aplicação)
UPDATE tb_empresa SET prefixo_mapa = 'Red'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao LIKE '%Redentor%';

UPDATE tb_empresa SET prefixo_mapa = 'Fut'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao LIKE '%Futuro%';

UPDATE tb_empresa SET prefixo_mapa = 'Bar'
WHERE (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '')
  AND descricao LIKE '%Barra%';

-- ---------------------------------------------------------------------------
-- 2) Contador independente por empresa (persiste após delete)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_mapa_seq (
    id_empresa  INT NOT NULL,
    ultimo_seq  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_empresa),
    CONSTRAINT fk_tb_mapa_seq_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 3) Colunas no MAPA: id_empresa + codigo_mapa
-- ---------------------------------------------------------------------------
SET @col_emp := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_map'
      AND COLUMN_NAME = 'id_empresa'
);

SET @sql := IF(
    @col_emp = 0,
    'ALTER TABLE tb_map ADD COLUMN id_empresa INT NULL COMMENT ''Empresa dona da sequência do código'' AFTER id_usuario',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_cod := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_map'
      AND COLUMN_NAME = 'codigo_mapa'
);

SET @sql := IF(
    @col_cod = 0,
    'ALTER TABLE tb_map ADD COLUMN codigo_mapa VARCHAR(20) NULL COMMENT ''Código de negócio (ex.: Red01)'' AFTER cod_map',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_cod := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_map'
      AND INDEX_NAME = 'uk_tb_map_codigo_mapa'
);

SET @sql := IF(
    @idx_cod = 0,
    'ALTER TABLE tb_map ADD UNIQUE KEY uk_tb_map_codigo_mapa (codigo_mapa)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_emp := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_map'
      AND INDEX_NAME = 'idx_tb_map_id_empresa'
);

SET @sql := IF(
    @idx_emp = 0,
    'ALTER TABLE tb_map ADD KEY idx_tb_map_id_empresa (id_empresa)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_emp := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_map'
      AND CONSTRAINT_NAME = 'fk_tb_map_empresa'
      AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);

SET @sql := IF(
    @fk_emp = 0,
    'ALTER TABLE tb_map ADD CONSTRAINT fk_tb_map_empresa FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- 4) Backfill id_empresa legados + inicializa sequências
--     (codigo_mapa legado é preenchido pelo script Python de aplicação)
-- ---------------------------------------------------------------------------
UPDATE tb_map m
LEFT JOIN tb_linha l_hdr ON l_hdr.id_linha = m.id_linha
LEFT JOIN tb_item_map i0 ON i0.id_item = (
    SELECT MIN(i2.id_item) FROM tb_item_map i2 WHERE i2.idmap = m.id_registro
)
LEFT JOIN tb_linha l_item ON l_item.id_linha = i0.id_linha
SET m.id_empresa = COALESCE(m.id_empresa, l_hdr.id_empresa, l_item.id_empresa)
WHERE m.id_empresa IS NULL;

INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq)
SELECT e.id_empresa, 0
FROM tb_empresa e
WHERE e.prefixo_mapa IS NOT NULL
  AND TRIM(e.prefixo_mapa) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM tb_mapa_seq s WHERE s.id_empresa = e.id_empresa
  );
