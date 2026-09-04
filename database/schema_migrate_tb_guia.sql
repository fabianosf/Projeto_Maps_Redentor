-- Migração: tb_guia — cadastro de guias de viagem
USE map;

CREATE TABLE IF NOT EXISTS tb_guia (
    id_guia       INT          NOT NULL AUTO_INCREMENT COMMENT 'Chave primária (idgui)',
    numero        VARCHAR(15)  NULL     COMMENT 'Número da guia (código de barras ou manual)',
    id_empresa    INT          NULL     COMMENT 'FK tb_empresa.id_empresa',
    id_linha      INT          NULL     COMMENT 'FK tb_linha.id_linha',
    id_turno      INT          NULL     COMMENT 'FK tb_turno.id_turno',
    id_veiculo    INT          NULL     COMMENT 'FK tb_veiculo.id_veiculo',
    id_motorista  INT          NULL     COMMENT 'FK tb_motorista.id_motorista',
    hor_ini       DATETIME     NULL     COMMENT 'Horário inicial (formato HH:MM na tela)',
    hor_fim       DATETIME     NULL     COMMENT 'Horário final (formato HH:MM na tela)',
    roleta01_ini  INT          NULL     COMMENT 'Roleta 01 inicial',
    roleta01_fim  INT          NULL     COMMENT 'Roleta 01 final',
    roleta2_ini   INT          NULL     COMMENT 'Roleta 02 inicial',
    roleta2_fim   INT          NULL     COMMENT 'Roleta 02 final',
    observacao    VARCHAR(150) NULL     COMMENT 'Observações',
    data          DATETIME     NULL     COMMENT 'Data e hora do cadastro da guia',
    PRIMARY KEY (id_guia),
    KEY idx_tb_guia_numero (numero),
    KEY idx_tb_guia_empresa (id_empresa),
    KEY idx_tb_guia_linha (id_linha),
    KEY idx_tb_guia_turno (id_turno),
    KEY idx_tb_guia_veiculo (id_veiculo),
    KEY idx_tb_guia_motorista (id_motorista),
    CONSTRAINT fk_tb_guia_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_tb_guia_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_guia_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_guia_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_guia_motorista
        FOREIGN KEY (id_motorista) REFERENCES tb_motorista (id_motorista)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
