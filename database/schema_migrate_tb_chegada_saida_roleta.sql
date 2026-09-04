-- Migração: tb_chegada_saida — roleta → roleta_01 + nova coluna roleta_02
USE map;

SET @has_roleta := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map'
      AND TABLE_NAME = 'tb_chegada_saida'
      AND COLUMN_NAME = 'roleta'
);

SET @sql_rename := IF(
    @has_roleta > 0,
    'ALTER TABLE tb_chegada_saida CHANGE COLUMN roleta roleta_01 INT NULL COMMENT ''Roleta 01''',
    'SELECT 1'
);
PREPARE stmt_rename FROM @sql_rename;
EXECUTE stmt_rename;
DEALLOCATE PREPARE stmt_rename;

ALTER TABLE tb_chegada_saida
    ADD COLUMN IF NOT EXISTS roleta_02 INT NULL
        COMMENT 'Roleta 02'
        AFTER roleta_01;
