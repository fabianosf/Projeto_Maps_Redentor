-- Migração: tb_reg_ponto → tb_map, tb_item_reg_ponto → tb_item_map
-- Colunas: codigo_registro → cod_map (tb_map), id_registro → idmap (tb_item_map)
-- Idempotente: ignora passos já aplicados

USE map;

SET @has_viagem_fk := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_viagem'
      AND CONSTRAINT_NAME = 'fk_tb_viagem_item_registro' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);
SET @sql := IF(@has_viagem_fk > 0,
    'ALTER TABLE tb_viagem DROP FOREIGN KEY fk_tb_viagem_item_registro',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_item_fk := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_reg_ponto'
      AND CONSTRAINT_NAME = 'fk_tb_item_registro_ponto_registro' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);
SET @sql := IF(@has_item_fk > 0,
    'ALTER TABLE tb_item_reg_ponto DROP FOREIGN KEY fk_tb_item_registro_ponto_registro',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @rename_item := (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_reg_ponto'
);
SET @sql := IF(@rename_item > 0,
    'RENAME TABLE tb_item_reg_ponto TO tb_item_map',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @rename_reg := (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_reg_ponto'
);
SET @sql := IF(@rename_reg > 0,
    'RENAME TABLE tb_reg_ponto TO tb_map',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_cod_map := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_map' AND COLUMN_NAME = 'cod_map'
);
SET @sql := IF(@has_cod_map = 0,
    'ALTER TABLE tb_map CHANGE COLUMN codigo_registro cod_map INT NOT NULL COMMENT ''Código de negócio''',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_old_uk := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_map' AND INDEX_NAME = 'uk_tb_reg_ponto_codigo'
);
SET @sql := IF(@has_old_uk > 0,
    'ALTER TABLE tb_map DROP INDEX uk_tb_reg_ponto_codigo',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_new_uk := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_map' AND INDEX_NAME = 'uk_tb_map_cod_map'
);
SET @sql := IF(@has_new_uk = 0,
    'ALTER TABLE tb_map ADD UNIQUE KEY uk_tb_map_cod_map (cod_map)',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_idmap := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'idmap'
);
SET @sql := IF(@has_idmap = 0,
    'ALTER TABLE tb_item_map CHANGE COLUMN id_registro idmap INT NOT NULL COMMENT ''FK tb_map.id_registro''',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_old_idx1 := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_map' AND INDEX_NAME = 'idx_tb_item_reg_ponto_registro'
);
SET @sql := IF(@has_old_idx1 > 0,
    'ALTER TABLE tb_item_map DROP INDEX idx_tb_item_reg_ponto_registro',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_old_idx2 := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_map' AND INDEX_NAME = 'idx_tb_item_registro_ponto_registro'
);
SET @sql := IF(@has_old_idx2 > 0,
    'ALTER TABLE tb_item_map DROP INDEX idx_tb_item_registro_ponto_registro',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_idmap_idx := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_map' AND INDEX_NAME = 'idx_tb_item_map_idmap'
);
SET @sql := IF(@has_idmap_idx = 0,
    'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_idmap (idmap)',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_item_map_fk := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_item_map'
      AND CONSTRAINT_NAME = 'fk_tb_item_map_map' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);
SET @sql := IF(@has_item_map_fk = 0,
    'ALTER TABLE tb_item_map ADD CONSTRAINT fk_tb_item_map_map FOREIGN KEY (idmap) REFERENCES tb_map (id_registro)',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_viagem_map_fk := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_viagem'
      AND CONSTRAINT_NAME = 'fk_tb_viagem_item_map' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);
SET @sql := IF(@has_viagem_map_fk = 0,
    'ALTER TABLE tb_viagem ADD CONSTRAINT fk_tb_viagem_item_map FOREIGN KEY (id_item_registro) REFERENCES tb_item_map (id_item)',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
