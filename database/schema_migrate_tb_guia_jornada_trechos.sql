-- Migração: Guia como jornada (motorista+empresa+data) + trechos + auditoria
-- Compatível com MariaDB 10.2+. Idempotente.
USE map;

-- ---------------------------------------------------------------------------
-- 1) Status e chegada no cabeçalho da guia
-- ---------------------------------------------------------------------------
SET @col_status := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia'
      AND COLUMN_NAME = 'status'
);

SET @sql := IF(
    @col_status = 0,
    'ALTER TABLE tb_guia ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT ''ABERTA'' COMMENT ''ABERTA|ENCERRADA'' AFTER observacao',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_chegada := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia'
      AND COLUMN_NAME = 'chegada_ponto'
);

SET @sql := IF(
    @col_chegada = 0,
    'ALTER TABLE tb_guia ADD COLUMN chegada_ponto DATETIME NULL COMMENT ''Chegada ao ponto na abertura'' AFTER hor_ini',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_status := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia'
      AND INDEX_NAME = 'idx_tb_guia_status'
);

SET @sql := IF(
    @idx_status = 0,
    'ALTER TABLE tb_guia ADD KEY idx_tb_guia_status (status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_mot_emp := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia'
      AND INDEX_NAME = 'idx_tb_guia_motorista_empresa_status'
);

SET @sql := IF(
    @idx_mot_emp = 0,
    'ALTER TABLE tb_guia ADD KEY idx_tb_guia_motorista_empresa_status (id_motorista, id_empresa, status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Backfill status a partir de hor_fim
UPDATE tb_guia
SET status = 'ENCERRADA'
WHERE hor_fim IS NOT NULL
  AND (status IS NULL OR status = '' OR status = 'ABERTA');

UPDATE tb_guia
SET status = 'ABERTA'
WHERE hor_fim IS NULL
  AND (status IS NULL OR status = '');

-- ---------------------------------------------------------------------------
-- 2) Trechos (viagens) dentro da mesma Guia
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_guia_trecho (
    id_trecho         INT          NOT NULL AUTO_INCREMENT,
    id_guia           INT          NOT NULL COMMENT 'FK tb_guia.id_guia',
    seq               INT          NOT NULL DEFAULT 1,
    id_linha          INT          NULL,
    id_veiculo        INT          NULL,
    id_local_origem   INT          NULL,
    id_local_destino  INT          NULL,
    sentido           VARCHAR(10)  NOT NULL DEFAULT 'IDA' COMMENT 'IDA|VOLTA',
    hor_ini           DATETIME     NULL,
    hor_fim           DATETIME     NULL,
    jae_ini           INT          NULL,
    jae_fim           INT          NULL,
    riocard_ini       INT          NULL,
    riocard_fim       INT          NULL,
    id_usuario        INT          NULL COMMENT 'Quem registrou',
    criado_em         DATETIME     NOT NULL,
    atualizado_em     DATETIME     NULL,
    PRIMARY KEY (id_trecho),
    KEY idx_tb_guia_trecho_guia (id_guia),
    KEY idx_tb_guia_trecho_linha (id_linha),
    KEY idx_tb_guia_trecho_veiculo (id_veiculo),
    CONSTRAINT fk_tb_guia_trecho_guia
        FOREIGN KEY (id_guia) REFERENCES tb_guia (id_guia),
    CONSTRAINT fk_tb_guia_trecho_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_guia_trecho_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 3) Auditoria de troca linha/carro/rota (sem encerrar a Guia)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_guia_alteracao (
    id_alteracao    INT          NOT NULL AUTO_INCREMENT,
    id_guia         INT          NOT NULL,
    id_usuario      INT          NOT NULL,
    campo           VARCHAR(30)  NOT NULL COMMENT 'linha|veiculo|rota',
    valor_anterior  VARCHAR(120) NULL,
    valor_novo      VARCHAR(120) NULL,
    motivo          VARCHAR(255) NOT NULL,
    registrado_em   DATETIME     NOT NULL,
    PRIMARY KEY (id_alteracao),
    KEY idx_tb_guia_alteracao_guia (id_guia),
    CONSTRAINT fk_tb_guia_alteracao_guia
        FOREIGN KEY (id_guia) REFERENCES tb_guia (id_guia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 4) Roleta pode referenciar trecho (somente se a tabela existir)
-- ---------------------------------------------------------------------------
SET @tbl_roleta := (
    SELECT COUNT(*)
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_roleta_leitura'
);

SET @col_trecho := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_roleta_leitura'
      AND COLUMN_NAME = 'id_trecho'
);

SET @sql := IF(
    @tbl_roleta > 0 AND @col_trecho = 0,
    'ALTER TABLE tb_guia_roleta_leitura ADD COLUMN id_trecho INT NULL COMMENT ''FK tb_guia_trecho'' AFTER id_guia',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_roleta_trecho := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_guia_roleta_leitura'
      AND INDEX_NAME = 'idx_tb_guia_roleta_trecho'
);

SET @sql := IF(
    @tbl_roleta > 0 AND @idx_roleta_trecho = 0,
    'ALTER TABLE tb_guia_roleta_leitura ADD KEY idx_tb_guia_roleta_trecho (id_trecho)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Backfill: cria trecho inicial para guias legadas sem trecho
INSERT INTO tb_guia_trecho (
    id_guia, seq, id_linha, id_veiculo, sentido, hor_ini, hor_fim,
    jae_ini, jae_fim, riocard_ini, riocard_fim, criado_em
)
SELECT
    g.id_guia,
    1,
    g.id_linha,
    g.id_veiculo,
    'IDA',
    g.hor_ini,
    g.hor_fim,
    g.roleta01_ini,
    g.roleta01_fim,
    g.roleta2_ini,
    g.roleta2_fim,
    COALESCE(g.data, NOW())
FROM tb_guia g
WHERE NOT EXISTS (
    SELECT 1 FROM tb_guia_trecho t WHERE t.id_guia = g.id_guia
)
AND (g.id_linha IS NOT NULL OR g.id_veiculo IS NOT NULL OR g.hor_ini IS NOT NULL);
