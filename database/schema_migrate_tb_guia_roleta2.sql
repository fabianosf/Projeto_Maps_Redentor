-- Migração: tb_guia — segunda roleta (ROLETA 02)
USE map;

ALTER TABLE tb_guia
    ADD COLUMN roleta2_ini INT NULL COMMENT 'Roleta 02 inicial' AFTER roleta01_fim,
    ADD COLUMN roleta2_fim INT NULL COMMENT 'Roleta 02 final' AFTER roleta2_ini;
