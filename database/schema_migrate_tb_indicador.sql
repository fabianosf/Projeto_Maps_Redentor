-- Migração: tb_indicador e tb_ind_perf — indicadores por perfil
USE map;

CREATE TABLE IF NOT EXISTS tb_indicador (
    id_ind     INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    cod_ind    INT         NOT NULL COMMENT 'Código do indicador',
    descricao  VARCHAR(20) NOT NULL COMMENT 'Sigla / nome curto do indicador',
    detalhe    VARCHAR(120) NULL COMMENT 'Descrição detalhada do indicador',
    PRIMARY KEY (id_ind),
    UNIQUE KEY uk_tb_indicador_cod_ind (cod_ind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_ind_perf (
    id_indperf INT NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    id_ind     INT NOT NULL COMMENT 'FK tb_indicador.id_ind',
    id_perfil  INT NOT NULL COMMENT 'FK tb_perfil.id_perfil',
    PRIMARY KEY (id_indperf),
    UNIQUE KEY uk_tb_ind_perf_ind_perfil (id_ind, id_perfil),
    KEY idx_tb_ind_perf_id_ind (id_ind),
    KEY idx_tb_ind_perf_id_perfil (id_perfil),
    CONSTRAINT fk_tb_ind_perf_indicador
        FOREIGN KEY (id_ind) REFERENCES tb_indicador (id_ind),
    CONSTRAINT fk_tb_ind_perf_perfil
        FOREIGN KEY (id_perfil) REFERENCES tb_perfil (id_perfil)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
