-- Migração: recria tb_map, tb_item_map e tb_viagem (inverso de schema_migrate_drop_map_viagem.sql)
USE map;

CREATE TABLE IF NOT EXISTS tb_map (
    id_registro         INT          NOT NULL AUTO_INCREMENT,
    cod_map             INT          NOT NULL COMMENT 'Código de negócio (1..99999)',
    id_usuario          INT          NOT NULL COMMENT 'FK tb_usuario.id_usuario (quem lançou)',
    id_linha            INT          NOT NULL COMMENT 'FK tb_linha.id_linha',
    id_turno            INT          NOT NULL COMMENT 'FK tb_turno.id_turno',
    data                DATE         NOT NULL,
    inicio_jornada_des  DATETIME     NOT NULL,
    fim_jornada_des     DATETIME     DEFAULT NULL,
    observacao          VARCHAR(500) DEFAULT NULL,
    PRIMARY KEY (id_registro),
    UNIQUE KEY uk_tb_map_cod_map (cod_map),
    KEY idx_tb_map_usuario (id_usuario),
    KEY idx_tb_map_linha (id_linha),
    KEY idx_tb_map_turno (id_turno),
    KEY idx_tb_map_data (data),
    KEY idx_tb_map_inicio (inicio_jornada_des),
    CONSTRAINT fk_tb_map_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_map_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_map_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_item_map (
    id_item        INT      NOT NULL AUTO_INCREMENT,
    idmap          INT      NOT NULL COMMENT 'FK tb_map.id_registro',
    id_veiculo     INT      NOT NULL COMMENT 'FK tb_veiculo.id_veiculo',
    id_motorista   INT      NOT NULL COMMENT 'FK tb_motorista.id_motorista',
    hor_ini_jor    DATETIME DEFAULT NULL,
    hor_fim_jor    DATETIME DEFAULT NULL,
    chegada_ponto  DATETIME DEFAULT NULL,
    PRIMARY KEY (id_item),
    KEY idx_tb_item_map_idmap (idmap),
    KEY idx_tb_item_map_veiculo (id_veiculo),
    KEY idx_tb_item_map_motorista (id_motorista),
    CONSTRAINT fk_tb_item_map_map
        FOREIGN KEY (idmap) REFERENCES tb_map (id_registro),
    CONSTRAINT fk_tb_item_map_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_item_map_motorista
        FOREIGN KEY (id_motorista) REFERENCES tb_motorista (id_motorista)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_viagem (
    id_viagem         INT         NOT NULL AUTO_INCREMENT,
    id_item_registro  INT         NOT NULL COMMENT 'FK tb_item_map.id_item',
    horario_chegada   DATETIME    NOT NULL,
    placa             VARCHAR(5)  DEFAULT NULL COMMENT 'HH:MM — campo Placa da UI (NÃO placa do veículo)',
    horario_saida     DATETIME    NOT NULL,
    intervalo         INT         DEFAULT NULL,
    qtd_pas_ida       INT         DEFAULT NULL,
    qtd_pas_volta     INT         DEFAULT NULL,
    PRIMARY KEY (id_viagem),
    KEY idx_tb_viagem_id_item_registro (id_item_registro),
    CONSTRAINT fk_tb_viagem_item_map
        FOREIGN KEY (id_item_registro) REFERENCES tb_item_map (id_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
