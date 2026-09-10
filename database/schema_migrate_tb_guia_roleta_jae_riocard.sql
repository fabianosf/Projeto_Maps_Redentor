-- Migração: leituras manuais Ja E / RioCard por viagem (Guia)
-- Não altera roleta01/roleta2 de tb_guia (legado preservado).
USE map;

CREATE TABLE IF NOT EXISTS tb_guia_roleta_leitura (
    id_leitura            INT          NOT NULL AUTO_INCREMENT,
    id_viagem             INT          NULL     COMMENT 'FK tb_viagem — preferencial',
    id_guia               INT          NULL     COMMENT 'FK tb_guia — quando sem viagem de mapa',
    id_veiculo            INT          NOT NULL COMMENT 'FK tb_veiculo',
    sentido               VARCHAR(5)   NOT NULL COMMENT 'ida | volta',
    fonte                 VARCHAR(10)  NOT NULL COMMENT 'jae | riocard',
    leitura_ini           INT          NULL     COMMENT 'Leitura inicial',
    leitura_fim           INT          NULL     COMMENT 'Leitura final',
    passageiros           INT          NULL     COMMENT 'Calculado (fim - ini; virada com wrap)',
    virada                TINYINT      NOT NULL DEFAULT 0 COMMENT '1 = contador reiniciou',
    justificativa_virada  VARCHAR(200) NULL,
    status_leitura        VARCHAR(20)  NOT NULL DEFAULT 'iniciada'
        COMMENT 'iniciada | finalizada',
    id_usuario            INT          NOT NULL COMMENT 'Responsável',
    criado_em             DATETIME     NOT NULL,
    atualizado_em         DATETIME     NOT NULL,
    PRIMARY KEY (id_leitura),
    UNIQUE KEY uk_guia_roleta_viagem_sentido_fonte (id_viagem, sentido, fonte),
    KEY idx_guia_roleta_guia (id_guia, sentido, fonte),
    KEY idx_guia_roleta_veiculo (id_veiculo, fonte, sentido, atualizado_em),
    KEY idx_guia_roleta_usuario (id_usuario),
    CONSTRAINT fk_guia_roleta_viagem
        FOREIGN KEY (id_viagem) REFERENCES tb_viagem (id_viagem),
    CONSTRAINT fk_guia_roleta_guia
        FOREIGN KEY (id_guia) REFERENCES tb_guia (id_guia),
    CONSTRAINT fk_guia_roleta_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_guia_roleta_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_guia_roleta_historico (
    id_historico     INT          NOT NULL AUTO_INCREMENT,
    id_leitura       INT          NOT NULL,
    acao             VARCHAR(20)  NOT NULL COMMENT 'iniciar | finalizar | alterar',
    leitura_ini      INT          NULL,
    leitura_fim      INT          NULL,
    passageiros      INT          NULL,
    virada           TINYINT      NULL,
    justificativa    VARCHAR(200) NULL,
    id_usuario       INT          NOT NULL,
    registrado_em    DATETIME     NOT NULL,
    PRIMARY KEY (id_historico),
    KEY idx_guia_roleta_hist_leitura (id_leitura),
    KEY idx_guia_roleta_hist_usuario (id_usuario),
    CONSTRAINT fk_guia_roleta_hist_leitura
        FOREIGN KEY (id_leitura) REFERENCES tb_guia_roleta_leitura (id_leitura)
        ON DELETE CASCADE,
    CONSTRAINT fk_guia_roleta_hist_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
