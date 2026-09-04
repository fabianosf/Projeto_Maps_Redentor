-- Migração: tb_guia — roleta_ini/fim → roleta01_ini/fim
USE map;

ALTER TABLE tb_guia
    CHANGE COLUMN roleta_ini roleta01_ini INT NULL COMMENT 'Roleta 01 inicial',
    CHANGE COLUMN roleta_fim roleta01_fim INT NULL COMMENT 'Roleta 01 final';
