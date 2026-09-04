-- Migração: texto livre da Tela Mensagem em tb_avaria
USE map;

ALTER TABLE tb_avaria
    ADD COLUMN IF NOT EXISTS texto VARCHAR(500) NULL COMMENT 'Texto livre da mensagem' AFTER data;
