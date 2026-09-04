-- Coluna detalhe em tb_indicador (descrição longa na Tela 10 — Indicadores)
USE map;

ALTER TABLE tb_indicador
    ADD COLUMN detalhe VARCHAR(120) NULL COMMENT 'Descrição detalhada do indicador'
    AFTER descricao;
