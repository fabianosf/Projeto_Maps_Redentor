-- Migração: tb_avaria — substitui autor por id_usuario (FK tb_usuario)
USE map;

SET @col_autor := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map'
      AND TABLE_NAME = 'tb_avaria'
      AND COLUMN_NAME = 'autor'
);

SET @sql_drop_autor := IF(
    @col_autor > 0,
    'ALTER TABLE tb_avaria DROP COLUMN autor',
    'SELECT 1'
);
PREPARE stmt FROM @sql_drop_autor;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_id_usuario := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'map'
      AND TABLE_NAME = 'tb_avaria'
      AND COLUMN_NAME = 'id_usuario'
);

SET @sql_add_id_usuario := IF(
    @col_id_usuario = 0,
    'ALTER TABLE tb_avaria
        ADD COLUMN id_usuario INT NOT NULL COMMENT ''FK tb_usuario.id_usuario'' AFTER id_tip,
        ADD KEY idx_tb_avaria_id_usuario (id_usuario),
        ADD CONSTRAINT fk_tb_avaria_usuario
            FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_id_usuario;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
