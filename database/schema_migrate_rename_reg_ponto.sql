-- Migração: renomeia tabelas operacionais de ponto
-- tb_registro_ponto      → tb_reg_ponto
-- tb_item_registro_ponto → tb_item_reg_ponto
-- InnoDB atualiza FKs automaticamente no RENAME TABLE

USE map;

-- Só executa se ainda existir o nome antigo
SET @rename_item := (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_registro_ponto'
);
SET @rename_reg := (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_registro_ponto'
);

SET @sql_item := IF(
    @rename_item > 0,
    'RENAME TABLE tb_item_registro_ponto TO tb_item_reg_ponto',
    'SELECT 1'
);
PREPARE stmt_item FROM @sql_item;
EXECUTE stmt_item;
DEALLOCATE PREPARE stmt_item;

SET @sql_reg := IF(
    @rename_reg > 0,
    'RENAME TABLE tb_registro_ponto TO tb_reg_ponto',
    'SELECT 1'
);
PREPARE stmt_reg FROM @sql_reg;
EXECUTE stmt_reg;
DEALLOCATE PREPARE stmt_reg;
