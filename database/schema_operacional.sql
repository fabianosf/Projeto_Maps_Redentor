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

-- Indicadores de operação e vínculo com perfis de usuário
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

-- Parâmetros de configuração da aplicação (chave/valor)
CREATE TABLE IF NOT EXISTS tb_configuracao (
    idconf INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária',
    chave  VARCHAR(15) NOT NULL COMMENT 'Código da chave',
    valor  VARCHAR(30) NOT NULL COMMENT 'Valor da chave',
    PRIMARY KEY (idconf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO tb_configuracao (chave, valor)
SELECT 'QTD_MAX_TENTATIVAS', '3' FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM tb_configuracao WHERE chave = 'QTD_MAX_TENTATIVAS'
);

-- Cadastro de guias de viagem (Tela 05 — Guia)
CREATE TABLE IF NOT EXISTS tb_guia (
    id_guia       INT          NOT NULL AUTO_INCREMENT COMMENT 'Chave primária (idgui)',
    numero        VARCHAR(15)  NULL     COMMENT 'Número da guia (código de barras ou manual)',
    id_empresa    INT          NULL     COMMENT 'FK tb_empresa.id_empresa',
    id_linha      INT          NULL     COMMENT 'FK tb_linha.id_linha',
    id_turno      INT          NULL     COMMENT 'FK tb_turno.id_turno',
    id_veiculo    INT          NULL     COMMENT 'FK tb_veiculo.id_veiculo',
    id_motorista  INT          NULL     COMMENT 'FK tb_motorista.id_motorista',
    hor_ini       DATETIME     NULL     COMMENT 'Horário inicial (formato HH:MM na tela)',
    hor_fim       DATETIME     NULL     COMMENT 'Horário final (formato HH:MM na tela)',
    roleta01_ini  INT          NULL     COMMENT 'Roleta 01 inicial',
    roleta01_fim  INT          NULL     COMMENT 'Roleta 01 final',
    roleta2_ini   INT          NULL     COMMENT 'Roleta 02 inicial',
    roleta2_fim   INT          NULL     COMMENT 'Roleta 02 final',
    observacao    VARCHAR(150) NULL     COMMENT 'Observações',
    data          DATETIME     NULL     COMMENT 'Data e hora do cadastro da guia',
    PRIMARY KEY (id_guia),
    KEY idx_tb_guia_numero (numero),
    KEY idx_tb_guia_empresa (id_empresa),
    KEY idx_tb_guia_linha (id_linha),
    KEY idx_tb_guia_turno (id_turno),
    KEY idx_tb_guia_veiculo (id_veiculo),
    KEY idx_tb_guia_motorista (id_motorista),
    CONSTRAINT fk_tb_guia_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_tb_guia_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_guia_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_guia_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_guia_motorista
        FOREIGN KEY (id_motorista) REFERENCES tb_motorista (id_motorista)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chegada e saída vinculadas à guia (Tela Chegada | Saída)
CREATE TABLE IF NOT EXISTS tb_chegada_saida (
    id_cs          INT         NOT NULL AUTO_INCREMENT COMMENT 'Chave primária (idcs)',
    id_gui         INT         NULL     COMMENT 'FK tb_guia.id_guia',
    id_linha       INT         NULL     COMMENT 'FK tb_linha.id_linha',
    carro          INT         NULL     COMMENT 'FK tb_veiculo.id_veiculo',
    evento         VARCHAR(1)  NULL     COMMENT 'C = chegada, S = saída',
    roleta_01      INT         NULL     COMMENT 'Roleta 01',
    roleta_02      INT         NULL     COMMENT 'Roleta 02',
    temperatura    INT         NULL     COMMENT 'Temperatura',
    linha_destino  INT         NULL     COMMENT 'Linha destino',
    destino        INT         NULL     COMMENT 'Destino',
    PRIMARY KEY (id_cs),
    KEY idx_tb_chegada_saida_gui (id_gui),
    KEY idx_tb_chegada_saida_linha (id_linha),
    KEY idx_tb_chegada_saida_carro (carro),
    KEY idx_tb_chegada_saida_evento (evento),
    CONSTRAINT fk_tb_chegada_saida_guia
        FOREIGN KEY (id_gui) REFERENCES tb_guia (id_guia),
    CONSTRAINT fk_tb_chegada_saida_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_chegada_saida_carro
        FOREIGN KEY (carro) REFERENCES tb_veiculo (id_veiculo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tipos e registros de avaria de veículo (Tela Mensagem)
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

-- MAPA operacional (cabeçalho → carros/itens → viagens)
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
