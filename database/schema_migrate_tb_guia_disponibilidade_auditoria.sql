-- Migração: disponibilidade motorista (status trecho), auditoria de edição e versão/conflito
-- Compatível com MariaDB 10.2+. Idempotente.
USE map;

-- ---------------------------------------------------------------------------
-- 1) Versão no cabeçalho da guia (optimistic lock)
-- ---------------------------------------------------------------------------
SET @col_versao_g := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia'
      AND COLUMN_NAME = 'versao'
);

SET @sql := IF(
    @col_versao_g = 0,
    'ALTER TABLE tb_guia ADD COLUMN versao INT NOT NULL DEFAULT 1 COMMENT ''Optimistic lock'' AFTER status',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- 2) Status + versão no trecho
-- ---------------------------------------------------------------------------
SET @col_st_t := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_trecho'
      AND COLUMN_NAME = 'status'
);

SET @sql := IF(
    @col_st_t = 0,
    'ALTER TABLE tb_guia_trecho ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT ''PLANEJADO'' COMMENT ''PLANEJADO|EM_TRANSITO|CONCLUIDO'' AFTER sentido',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_versao_t := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_trecho'
      AND COLUMN_NAME = 'versao'
);

SET @sql := IF(
    @col_versao_t = 0,
    'ALTER TABLE tb_guia_trecho ADD COLUMN versao INT NOT NULL DEFAULT 1 COMMENT ''Optimistic lock'' AFTER atualizado_em',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_trecho_status := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_trecho'
      AND INDEX_NAME = 'idx_tb_guia_trecho_status'
);

SET @sql := IF(
    @idx_trecho_status = 0,
    'ALTER TABLE tb_guia_trecho ADD KEY idx_tb_guia_trecho_status (status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Backfill status do trecho
UPDATE tb_guia_trecho
SET status = 'CONCLUIDO'
WHERE hor_fim IS NOT NULL
  AND (status IS NULL OR status = '' OR status = 'PLANEJADO' OR status = 'EM_TRANSITO');

UPDATE tb_guia_trecho
SET status = 'EM_TRANSITO'
WHERE hor_fim IS NULL
  AND hor_ini IS NOT NULL
  AND (status IS NULL OR status = '' OR status = 'PLANEJADO');

UPDATE tb_guia_trecho
SET status = 'PLANEJADO'
WHERE hor_ini IS NULL
  AND hor_fim IS NULL
  AND (status IS NULL OR status = '');

-- ---------------------------------------------------------------------------
-- 3) Auditoria genérica de edição (campo já salvo)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_guia_auditoria (
    id_auditoria    INT          NOT NULL AUTO_INCREMENT,
    entidade        VARCHAR(30)  NOT NULL COMMENT 'guia|trecho|roleta',
    id_entidade     INT          NOT NULL,
    id_guia         INT          NULL,
    id_usuario      INT          NOT NULL,
    campo           VARCHAR(60)  NOT NULL,
    valor_anterior  VARCHAR(255) NULL,
    valor_novo      VARCHAR(255) NULL,
    motivo          VARCHAR(255) NOT NULL,
    registrado_em   DATETIME     NOT NULL,
    PRIMARY KEY (id_auditoria),
    KEY idx_tb_guia_auditoria_guia (id_guia),
    KEY idx_tb_guia_auditoria_entidade (entidade, id_entidade),
    CONSTRAINT fk_tb_guia_auditoria_guia
        FOREIGN KEY (id_guia) REFERENCES tb_guia (id_guia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 4) Versão na roleta (se a tabela existir)
-- ---------------------------------------------------------------------------
SET @tbl_roleta := (
    SELECT COUNT(*)
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_roleta_leitura'
);

SET @col_versao_r := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_roleta_leitura'
      AND COLUMN_NAME = 'versao'
);

SET @sql := IF(
    @tbl_roleta > 0 AND @col_versao_r = 0,
    'ALTER TABLE tb_guia_roleta_leitura ADD COLUMN versao INT NOT NULL DEFAULT 1 COMMENT ''Optimistic lock'' AFTER atualizado_em',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
