-- Migração: (2) origem/destino → FK tb_local; (3) remove idemp de tb_regp
USE map;

SET FOREIGN_KEY_CHECKS = 0;

-- Limpa dependentes para permitir recriação estrutural
DROP TABLE IF EXISTS tb_iregp;
DROP TABLE IF EXISTS tb_regp;
DROP TABLE IF EXISTS tb_linha;

CREATE TABLE tb_linha (
    idlin          INT          NOT NULL AUTO_INCREMENT,
    codlin         INT          NOT NULL COMMENT 'Código de negócio da linha',
    idemp          INT          NOT NULL COMMENT 'FK tb_empresa.idemp',
    idloc          INT          NULL     COMMENT 'FK tb_local.idloc (terminal/base principal)',
    descl          VARCHAR(150) NOT NULL COMMENT 'Descrição da linha',
    idloc_origem   INT          NOT NULL COMMENT 'FK tb_local.idloc (origem)',
    idloc_destino  INT          NOT NULL COMMENT 'FK tb_local.idloc (destino)',
    PRIMARY KEY (idlin),
    UNIQUE KEY uk_tb_linha_codlin (codlin),
    KEY idx_tb_linha_idemp (idemp),
    KEY idx_tb_linha_idloc (idloc),
    KEY idx_tb_linha_idloc_origem (idloc_origem),
    KEY idx_tb_linha_idloc_destino (idloc_destino),
    CONSTRAINT fk_tb_linha_empresa
        FOREIGN KEY (idemp) REFERENCES tb_empresa (idemp),
    CONSTRAINT fk_tb_linha_local
        FOREIGN KEY (idloc) REFERENCES tb_local (idloc),
    CONSTRAINT fk_tb_linha_origem
        FOREIGN KEY (idloc_origem) REFERENCES tb_local (idloc),
    CONSTRAINT fk_tb_linha_destino
        FOREIGN KEY (idloc_destino) REFERENCES tb_local (idloc)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recria tb_regp sem idemp
DROP TABLE IF EXISTS tb_regp;

CREATE TABLE tb_regp (
    idreg   INT         NOT NULL AUTO_INCREMENT,
    codreg  INT         NOT NULL COMMENT 'Código de negócio do registro de ponto',
    idlin   INT         NOT NULL COMMENT 'FK tb_linha.idlin',
    idtur   INT         NOT NULL COMMENT 'FK tb_turno.idtur',
    idmot   INT         NOT NULL COMMENT 'FK tb_motorista.idmot',
    ijor    TIME        NOT NULL COMMENT 'Início da jornada HH:MM',
    fjor    TIME        NOT NULL COMMENT 'Fim da jornada HH:MM',
    data    DATE        NOT NULL COMMENT 'Data do registro',
    PRIMARY KEY (idreg),
    UNIQUE KEY uk_tb_regp_codreg (codreg),
    KEY idx_tb_regp_idlin (idlin),
    KEY idx_tb_regp_idtur (idtur),
    KEY idx_tb_regp_idmot (idmot),
    KEY idx_tb_regp_data (data),
    CONSTRAINT fk_tb_regp_linha
        FOREIGN KEY (idlin) REFERENCES tb_linha (idlin),
    CONSTRAINT fk_tb_regp_turno
        FOREIGN KEY (idtur) REFERENCES tb_turno (idtur),
    CONSTRAINT fk_tb_regp_motorista
        FOREIGN KEY (idmot) REFERENCES tb_motorista (idmot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tb_iregp (
    idireg  INT           NOT NULL AUTO_INCREMENT,
    idreg   INT           NOT NULL COMMENT 'FK tb_regp.idreg',
    idvei   INT           NOT NULL COMMENT 'FK tb_veic.idvei',
    idmot   INT           NOT NULL COMMENT 'FK tb_motorista.idmot',
    sp      TIME          NOT NULL COMMENT 'Saída do ponto (local) HH:MM',
    cp      TIME          NOT NULL COMMENT 'Chegada no ponto (local) HH:MM',
    tplaca  DECIMAL(12,4) NOT NULL DEFAULT 0 COMMENT 'Valor numérico para cálculo posterior',
    PRIMARY KEY (idireg),
    KEY idx_tb_iregp_idreg (idreg),
    KEY idx_tb_iregp_idvei (idvei),
    KEY idx_tb_iregp_idmot (idmot),
    CONSTRAINT fk_tb_iregp_regp
        FOREIGN KEY (idreg) REFERENCES tb_regp (idreg),
    CONSTRAINT fk_tb_iregp_veic
        FOREIGN KEY (idvei) REFERENCES tb_veic (idvei),
    CONSTRAINT fk_tb_iregp_motorista
        FOREIGN KEY (idmot) REFERENCES tb_motorista (idmot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
