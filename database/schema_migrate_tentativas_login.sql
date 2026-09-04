-- Migração: remove coluna tentativas_login (contador passou a ser em memória)
-- e garante parâmetro QTD_MAX_TENTATIVAS em tb_configuracao
USE map;

SET @has_col := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map'
      AND TABLE_NAME = 'tb_usuario'
      AND COLUMN_NAME = 'tentativas_login'
);

SET @sql := IF(
    @has_col > 0,
    'ALTER TABLE tb_usuario DROP COLUMN tentativas_login',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT INTO tb_configuracao (chave, valor)
SELECT 'QTD_MAX_TENTATIVAS', '3' FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM tb_configuracao WHERE chave = 'QTD_MAX_TENTATIVAS'
);
