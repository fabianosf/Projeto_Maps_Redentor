-- Migração: tabela tb_configuracao (parâmetros chave/valor)
USE map;

CREATE TABLE IF NOT EXISTS tb_configuracao (
    idconf INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    chave  VARCHAR(15) NOT NULL COMMENT 'Código da chave',
    valor  VARCHAR(30) NOT NULL COMMENT 'Valor da chave',
    PRIMARY KEY (idconf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
