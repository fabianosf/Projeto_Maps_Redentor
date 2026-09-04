-- Migração: tb_chegada_saida — registros de chegada e saída vinculados à guia
USE map;

CREATE TABLE IF NOT EXISTS tb_chegada_saida (
    id_cs          INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária (idcs)',
    id_gui         INT         NULL     COMMENT 'FK tb_guia.id_guia',
    id_linha       INT         NULL     COMMENT 'FK tb_linha.id_linha',
    carro          INT         NULL     COMMENT 'FK tb_veiculo.id_veiculo',
    evento         VARCHAR(1)  NULL     COMMENT 'C = chegada, S = saída',
    roleta_01      INT         NULL     COMMENT 'Roleta 01',
    roleta_02      INT         NULL     COMMENT 'Roleta 02',
    temperatura    INT         NULL     COMMENT 'Temperatura',
    linha_destino  INT         NULL     COMMENT 'Linha destino',
    destino        INT         NULL     COMMENT 'Destino',
    PRIMARY KEY (id_cs),
    KEY idx_tb_chegada_saida_gui (id_gui),
    KEY idx_tb_chegada_saida_linha (id_linha),
    KEY idx_tb_chegada_saida_carro (carro),
    KEY idx_tb_chegada_saida_evento (evento),
    CONSTRAINT fk_tb_chegada_saida_guia
        FOREIGN KEY (id_gui) REFERENCES tb_guia (id_guia),
    CONSTRAINT fk_tb_chegada_saida_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_chegada_saida_carro
        FOREIGN KEY (carro) REFERENCES tb_veiculo (id_veiculo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
