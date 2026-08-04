-- Tabelas operacionais MAP
-- Critérios: nomenclatura clara, tipos adequados, FKs pela PK, normalização 3FN
-- Executar após schema.sql

USE map;

CREATE TABLE IF NOT EXISTS tb_empresa (
    id_empresa      INT          NOT NULL AUTO_INCREMENT,
    codigo_empresa  INT          NOT NULL COMMENT 'Código de negócio',
    descricao       VARCHAR(100) NOT NULL,
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_empresa),
    UNIQUE KEY uk_tb_empresa_codigo (codigo_empresa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_motorista (
    id_motorista    INT          NOT NULL AUTO_INCREMENT,
    matricula       VARCHAR(20)  NOT NULL,
    nome            VARCHAR(150) NOT NULL,
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_motorista),
    UNIQUE KEY uk_tb_motorista_matricula (matricula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_local (
    id_local        INT          NOT NULL AUTO_INCREMENT,
    codigo_local    INT          NOT NULL COMMENT 'Código de negócio',
    descricao       VARCHAR(100) NOT NULL,
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_local),
    UNIQUE KEY uk_tb_local_codigo (codigo_local)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Linha: origem e destino são FKs; sem coluna "base" redundante com origem
CREATE TABLE IF NOT EXISTS tb_linha (
    id_linha         INT          NOT NULL AUTO_INCREMENT,
    codigo_linha     INT          NOT NULL COMMENT 'Código de negócio',
    id_empresa       INT          NOT NULL COMMENT 'FK tb_empresa.id_empresa',
    descricao        VARCHAR(150) NOT NULL,
    id_local_origem  INT          NOT NULL COMMENT 'FK tb_local.id_local',
    id_local_destino INT          NOT NULL COMMENT 'FK tb_local.id_local',
    ativo            TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_linha),
    UNIQUE KEY uk_tb_linha_codigo (codigo_linha),
    KEY idx_tb_linha_id_empresa (id_empresa),
    KEY idx_tb_linha_origem (id_local_origem),
    KEY idx_tb_linha_destino (id_local_destino),
    CONSTRAINT fk_tb_linha_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_tb_linha_origem
        FOREIGN KEY (id_local_origem) REFERENCES tb_local (id_local),
    CONSTRAINT fk_tb_linha_destino
        FOREIGN KEY (id_local_destino) REFERENCES tb_local (id_local)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_turno (
    id_turno        INT          NOT NULL AUTO_INCREMENT,
    codigo_turno    INT          NOT NULL COMMENT 'Código de negócio',
    descricao       VARCHAR(100) NOT NULL,
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_turno),
    UNIQUE KEY uk_tb_turno_codigo (codigo_turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_veiculo (
    id_veiculo      INT          NOT NULL AUTO_INCREMENT,
    codigo_veiculo  INT          NOT NULL COMMENT 'Código de negócio',
    numero_frota    VARCHAR(20)  NOT NULL COMMENT 'Número/prefixo na frota',
    placa           VARCHAR(10)  NOT NULL COMMENT 'Placa (Mercosul até 7 caracteres)',
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_veiculo),
    UNIQUE KEY uk_tb_veiculo_codigo (codigo_veiculo),
    UNIQUE KEY uk_tb_veiculo_numero (numero_frota),
    UNIQUE KEY uk_tb_veiculo_placa (placa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cabeçalho da jornada (MAP): empresa via linha (JOIN); motorista/veículo só no item
CREATE TABLE IF NOT EXISTS tb_map (
    id_registro       INT          NOT NULL AUTO_INCREMENT,
    cod_map           INT          NOT NULL COMMENT 'Código de negócio',
    id_usuario        INT          NOT NULL COMMENT 'FK tb_usuario.id_usuario (quem lançou)',
    id_linha          INT          NOT NULL COMMENT 'FK tb_linha.id_linha',
    id_turno          INT          NOT NULL COMMENT 'FK tb_turno.id_turno',
    data              DATE         NOT NULL COMMENT 'Data do registro (somente data; exibir DD/MM/AAAA na tela)',
    inicio_jornada_des DATETIME     NOT NULL COMMENT 'Início da jornada (desejado/planejado)',
    fim_jornada_des    DATETIME     NULL COMMENT 'Fim da jornada (desejado/planejado) — opcional',
    observacao        VARCHAR(500) NULL     COMMENT 'Comentários opcionais',
    PRIMARY KEY (id_registro),
    UNIQUE KEY uk_tb_map_cod_map (cod_map),
    KEY idx_tb_map_usuario (id_usuario),
    KEY idx_tb_map_linha (id_linha),
    KEY idx_tb_map_turno (id_turno),
    KEY idx_tb_map_data (data),
    KEY idx_tb_map_inicio (inicio_jornada_des),
    CONSTRAINT fk_tb_map_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario),
    CONSTRAINT fk_tb_map_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_map_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Detalhe do MAP: veículo, motorista e horários por item
CREATE TABLE IF NOT EXISTS tb_item_map (
    id_item        INT      NOT NULL AUTO_INCREMENT,
    idmap          INT      NOT NULL COMMENT 'FK tb_map.id_registro',
    id_veiculo     INT      NOT NULL COMMENT 'FK tb_veiculo.id_veiculo',
    id_motorista   INT      NOT NULL COMMENT 'FK tb_motorista.id_motorista',
    hor_ini_jor    DATETIME NULL COMMENT 'Início da jornada no item',
    hor_fim_jor    DATETIME NULL COMMENT 'Fim da jornada no item',
    chegada_ponto  DATETIME NULL COMMENT 'Chegada no ponto',
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

-- Viagens vinculadas a um item do MAP
CREATE TABLE IF NOT EXISTS tb_viagem (
    id_viagem         INT      NOT NULL AUTO_INCREMENT,
    id_item_registro  INT      NOT NULL COMMENT 'FK tb_item_map.id_item',
    horario_chegada   DATETIME NOT NULL COMMENT 'Horário de chegada da viagem',
    horario_saida     DATETIME NOT NULL COMMENT 'Horário de saída da viagem',
    placa             VARCHAR(5) NULL COMMENT 'Horário auxiliar HH:MM (campo Placa da UI)',
    intervalo         INT      NULL     COMMENT 'Intervalo (minutos ou unidade de negócio)',
    qtd_pas_ida       INT      NULL     COMMENT 'Quantidade de passageiros na ida',
    qtd_pas_volta     INT      NULL     COMMENT 'Quantidade de passageiros na volta',
    PRIMARY KEY (id_viagem),
    KEY idx_tb_viagem_id_item_registro (id_item_registro),
    CONSTRAINT fk_tb_viagem_item_map
        FOREIGN KEY (id_item_registro) REFERENCES tb_item_map (id_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
