-- Migração: tb_tip_avaria e tb_avaria — tipos e registros de avaria de veículo
USE map;

CREATE TABLE IF NOT EXISTS tb_tip_avaria (
    id_tip    INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    descricao VARCHAR(30) NOT NULL COMMENT 'Descrição do tipo de avaria',
    PRIMARY KEY (id_tip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_avaria (
    id_av      INT      NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    id_vei     INT      NOT NULL COMMENT 'FK tb_veiculo.id_veiculo',
    id_tip     INT      NOT NULL COMMENT 'FK tb_tip_avaria.id_tip',
    id_usuario INT      NOT NULL COMMENT 'FK tb_usuario.id_usuario',
    data       DATETIME NOT NULL COMMENT 'Data/hora (formato yyyy-MM-dd HH:mm:ss)',
    PRIMARY KEY (id_av),
    KEY idx_tb_avaria_id_vei (id_vei),
    KEY idx_tb_avaria_id_tip (id_tip),
    KEY idx_tb_avaria_id_usuario (id_usuario),
    KEY idx_tb_avaria_data (data),
    CONSTRAINT fk_tb_avaria_veiculo
        FOREIGN KEY (id_vei) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_avaria_tip_avaria
        FOREIGN KEY (id_tip) REFERENCES tb_tip_avaria (id_tip),
    CONSTRAINT fk_tb_avaria_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
