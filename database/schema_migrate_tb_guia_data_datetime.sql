-- Migração: tb_guia.data → DATETIME (data/hora do cadastro da guia)
USE map;

ALTER TABLE tb_guia
    MODIFY COLUMN data DATETIME NULL
        COMMENT 'Data e hora do cadastro da guia';
