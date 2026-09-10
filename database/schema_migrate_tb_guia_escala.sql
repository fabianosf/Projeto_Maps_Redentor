-- Migração: vínculo Guia ↔ escala (item) + auditoria de alteração de escala
USE map;

ALTER TABLE tb_guia
    ADD COLUMN IF NOT EXISTS id_item_map INT NULL
        COMMENT 'FK opcional tb_item_map.id_item (escala de origem)' AFTER id_motorista;

-- Índice / FK (idempotente via procedure simples omitida — aplicar se não existir)
ALTER TABLE tb_guia
    ADD KEY idx_tb_guia_item_map (id_item_map);

CREATE TABLE IF NOT EXISTS tb_escala_alteracao (
    id_alteracao   INT          NOT NULL AUTO_INCREMENT,
    id_item        INT          NOT NULL COMMENT 'FK tb_item_map.id_item',
    id_usuario     INT          NOT NULL COMMENT 'Quem alterou',
    justificativa  VARCHAR(300) NOT NULL,
    campo          VARCHAR(40)  NOT NULL COMMENT 'veiculo|motorista|hor_ini_jor|hor_fim_jor|chegada_ponto',
    valor_anterior VARCHAR(120) NULL,
    valor_novo     VARCHAR(120) NULL,
    registrado_em  DATETIME     NOT NULL,
    PRIMARY KEY (id_alteracao),
    KEY idx_escala_alt_item (id_item),
    KEY idx_escala_alt_usuario (id_usuario),
    CONSTRAINT fk_escala_alt_item
        FOREIGN KEY (id_item) REFERENCES tb_item_map (id_item),
    CONSTRAINT fk_escala_alt_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
