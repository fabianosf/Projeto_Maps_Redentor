-- Migração: horário HH:MM na chegada/saída
USE map;

ALTER TABLE tb_chegada_saida
    ADD COLUMN IF NOT EXISTS horario VARCHAR(5) NULL COMMENT 'Horário HH:MM' AFTER evento;
