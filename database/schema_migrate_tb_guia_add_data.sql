-- Migração: adiciona coluna data em tb_guia (última coluna)
USE map;

ALTER TABLE tb_guia
    ADD COLUMN IF NOT EXISTS data DATETIME NULL
        COMMENT 'Data e hora do cadastro da guia'
        AFTER observacao;
