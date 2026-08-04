-- Migração: codreg em tb_regp + tb_veic + tb_iregp
-- Executar em banco já existente (map)

USE map;

-- tb_regp: código de negócio para vínculo com tb_iregp
ALTER TABLE tb_regp
    ADD COLUMN IF NOT EXISTS codreg INT NULL COMMENT 'Código do registro de ponto' AFTER idreg;

UPDATE tb_regp SET codreg = idreg + 1000 WHERE codreg IS NULL;

ALTER TABLE tb_regp
    MODIFY codreg INT NOT NULL,
    ADD UNIQUE KEY IF NOT EXISTS uk_tb_regp_codreg (codreg);

-- tb_veic
CREATE TABLE IF NOT EXISTS tb_veic (
    idvei   INT          NOT NULL AUTO_INCREMENT,
    codvei  INT          NOT NULL COMMENT 'Código do veículo',
    numero  VARCHAR(20)  NOT NULL COMMENT 'Número/prefixo do veículo na frota',
    placa   VARCHAR(10)  NOT NULL COMMENT 'Placa do veículo',
    PRIMARY KEY (idvei),
    UNIQUE KEY uk_tb_veic_codvei (codvei),
    UNIQUE KEY uk_tb_veic_numero (numero),
    UNIQUE KEY uk_tb_veic_placa (placa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- tb_iregp
CREATE TABLE IF NOT EXISTS tb_iregp (
    idireg  INT           NOT NULL AUTO_INCREMENT,
    codreg  INT           NOT NULL COMMENT 'FK tb_regp.codreg',
    codvei  INT           NOT NULL COMMENT 'FK tb_veic.codvei',
    codmot  VARCHAR(20)   NOT NULL COMMENT 'FK tb_motorista.matricula',
    sp      TIME          NOT NULL COMMENT 'Saída do ponto (local) HH:MM',
    cp      TIME          NOT NULL COMMENT 'Chegada no ponto (local) HH:MM',
    tplaca  DECIMAL(12,4) NOT NULL DEFAULT 0 COMMENT 'Valor numérico para cálculo posterior',
    PRIMARY KEY (idireg),
    KEY idx_tb_iregp_codreg (codreg),
    KEY idx_tb_iregp_codvei (codvei),
    KEY idx_tb_iregp_codmot (codmot),
    CONSTRAINT fk_tb_iregp_regp
        FOREIGN KEY (codreg) REFERENCES tb_regp (codreg),
    CONSTRAINT fk_tb_iregp_veic
        FOREIGN KEY (codvei) REFERENCES tb_veic (codvei),
    CONSTRAINT fk_tb_iregp_motorista
        FOREIGN KEY (codmot) REFERENCES tb_motorista (matricula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
