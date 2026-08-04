-- Migração: adiciona id_usuario, data e observacao em tb_reg_ponto
USE map;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS tb_item_reg_ponto;
DROP TABLE IF EXISTS tb_reg_ponto;

CREATE TABLE tb_reg_ponto (
    id_registro       INT          NOT NULL AUTO_INCREMENT,
    codigo_registro   INT          NOT NULL COMMENT 'Código de negócio',
    id_usuario        INT          NOT NULL COMMENT 'FK tb_usuario.id_usuario (quem lançou)',
    id_linha          INT          NOT NULL COMMENT 'FK tb_linha.id_linha',
    id_turno          INT          NOT NULL COMMENT 'FK tb_turno.id_turno',
    id_motorista      INT          NOT NULL COMMENT 'FK tb_motorista.id_motorista',
    id_veiculo        INT          NOT NULL COMMENT 'FK tb_veiculo.id_veiculo',
    data              DATE         NOT NULL COMMENT 'Data do registro (somente data; exibir DD/MM/AAAA na tela)',
    inicio_jornada    DATETIME     NOT NULL COMMENT 'Início (data + hora)',
    fim_jornada       DATETIME     NOT NULL COMMENT 'Fim (data + hora)',
    observacao        VARCHAR(500) NULL     COMMENT 'Comentários opcionais',
    PRIMARY KEY (id_registro),
    UNIQUE KEY uk_tb_reg_ponto_codigo (codigo_registro),
    KEY idx_tb_reg_ponto_usuario (id_usuario),
    KEY idx_tb_reg_ponto_linha (id_linha),
    KEY idx_tb_reg_ponto_turno (id_turno),
    KEY idx_tb_reg_ponto_motorista (id_motorista),
    KEY idx_tb_reg_ponto_veiculo (id_veiculo),
    KEY idx_tb_reg_ponto_data (data),
    KEY idx_tb_reg_ponto_inicio (inicio_jornada),
    CONSTRAINT fk_tb_reg_ponto_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario),
    CONSTRAINT fk_tb_reg_ponto_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_reg_ponto_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_reg_ponto_motorista
        FOREIGN KEY (id_motorista) REFERENCES tb_motorista (id_motorista),
    CONSTRAINT fk_tb_reg_ponto_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tb_item_reg_ponto (
    id_item           INT           NOT NULL AUTO_INCREMENT,
    id_registro       INT           NOT NULL COMMENT 'FK tb_reg_ponto.id_registro',
    id_local          INT           NOT NULL COMMENT 'FK tb_local.id_local (ponto da parada)',
    saida_ponto       DATETIME      NOT NULL COMMENT 'Saída do local',
    chegada_ponto     DATETIME      NOT NULL COMMENT 'Chegada no local',
    valor_calculo     DECIMAL(12,4) NOT NULL DEFAULT 0 COMMENT 'Valor para cálculo posterior',
    PRIMARY KEY (id_item),
    KEY idx_tb_item_reg_ponto_registro (id_registro),
    KEY idx_tb_item_reg_ponto_local (id_local),
    CONSTRAINT fk_tb_item_reg_ponto_registro
        FOREIGN KEY (id_registro) REFERENCES tb_reg_ponto (id_registro),
    CONSTRAINT fk_tb_item_reg_ponto_local
        FOREIGN KEY (id_local) REFERENCES tb_local (id_local)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
