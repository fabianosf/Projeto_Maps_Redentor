-- Migração: apenas coluna trocar_senha (remove colunas extras, se existirem)
USE map;

-- Renomeia deve_trocar_senha → trocar_senha, se a coluna antiga existir
SET @has_deve := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'deve_trocar_senha'
);
SET @has_trocar := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'trocar_senha'
);

SET @sql := IF(
    @has_deve > 0 AND @has_trocar = 0,
    'ALTER TABLE tb_usuario CHANGE COLUMN deve_trocar_senha trocar_senha TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''1 = primeiro acesso / troca obrigatória''',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Se nenhuma das duas existir, cria trocar_senha
SET @has_trocar := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'trocar_senha'
);
SET @sql := IF(
    @has_trocar = 0,
    'ALTER TABLE tb_usuario ADD COLUMN trocar_senha TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''1 = primeiro acesso / troca obrigatória'' AFTER ativo',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Remove colunas extras, se existirem
SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'senha_alterada_em') > 0,
    'ALTER TABLE tb_usuario DROP COLUMN senha_alterada_em',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'criado_em') > 0,
    'ALTER TABLE tb_usuario DROP COLUMN criado_em',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índice
SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND INDEX_NAME = 'idx_tb_usuario_trocar_senha') = 0,
    'ALTER TABLE tb_usuario ADD KEY idx_tb_usuario_trocar_senha (trocar_senha)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Remove índice antigo, se existir
SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_usuario' AND INDEX_NAME = 'idx_tb_usuario_deve_trocar') > 0,
    'ALTER TABLE tb_usuario DROP KEY idx_tb_usuario_deve_trocar',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE tb_usuario
SET trocar_senha = 0
WHERE matricula IN ('1001', '1002');
