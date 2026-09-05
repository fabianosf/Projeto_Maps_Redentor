-- Setup completo do banco MAP — PostgreSQL (espelho de schema.sql + schema_operacional.sql
-- + colunas das migrações finais: tb_chegada_saida.horario, tb_avaria.texto)
--
-- Conversões vs MariaDB:
--   AUTO_INCREMENT → SERIAL
--   TINYINT(1)     → BOOLEAN
--   DATETIME       → TIMESTAMP
--   ENGINE/CHARSET → removidos (UTF8 via encoding do banco)
--   ON DUPLICATE KEY UPDATE → ON CONFLICT ... DO UPDATE
--   FROM DUAL → omitido
--
-- Locales Linux: pt_BR.UTF-8 (não usar Portuguese_Brazil.1252 do Windows).
--
-- Aplicação (do zero):
--   createdb -h localhost -p 5432 -U fabianosf map
--   psql -h localhost -p 5432 -U fabianosf -d map -f database/schema_postgresql.sql
--
-- Política de senha (tb_usuario.senha): hash bcrypt cost 12 (igual MariaDB).
-- Admin seed: matrícula 59817 / senha 123.

SELECT 'Conecte-se ao banco map (ou rode CREATE DATABASE abaixo como superuser/createdb).'
  WHERE current_database() <> 'map';

-- Criação do banco (executar conectado a postgres se map ainda não existir):
-- CREATE DATABASE map
--   WITH ENCODING 'UTF8'
--        LC_COLLATE 'pt_BR.UTF-8'
--        LC_CTYPE 'pt_BR.UTF-8'
--        TEMPLATE template0;

-- \c map

-- ---------------------------------------------------------------------------
-- Autenticação / perfis
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_perfil (
    id_perfil       SERIAL       PRIMARY KEY,
    codigo_perfil   INT          NOT NULL,
    descricao       VARCHAR(100) NOT NULL,
    CONSTRAINT uk_tb_perfil_codigo UNIQUE (codigo_perfil)
);

-- Cadastros mestres (antes de tb_usuario por causa das FKs de vínculo)
CREATE TABLE IF NOT EXISTS tb_empresa (
    id_empresa      SERIAL       PRIMARY KEY,
    codigo_empresa  INT          NOT NULL,
    descricao       VARCHAR(100) NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_empresa_codigo UNIQUE (codigo_empresa)
);

CREATE TABLE IF NOT EXISTS tb_motorista (
    id_motorista    SERIAL       PRIMARY KEY,
    matricula       VARCHAR(20)  NOT NULL,
    nome            VARCHAR(150) NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_motorista_matricula UNIQUE (matricula)
);

CREATE TABLE IF NOT EXISTS tb_local (
    id_local        SERIAL       PRIMARY KEY,
    codigo_local    INT          NOT NULL,
    descricao       VARCHAR(100) NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_local_codigo UNIQUE (codigo_local)
);

CREATE TABLE IF NOT EXISTS tb_turno (
    id_turno        SERIAL       PRIMARY KEY,
    codigo_turno    INT          NOT NULL,
    descricao       VARCHAR(100) NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_turno_codigo UNIQUE (codigo_turno)
);

CREATE TABLE IF NOT EXISTS tb_veiculo (
    id_veiculo      SERIAL       PRIMARY KEY,
    codigo_veiculo  INT          NOT NULL,
    numero_frota    VARCHAR(20)  NOT NULL,
    placa           VARCHAR(10)  NOT NULL,
    id_empresa      INT          NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_veiculo_codigo UNIQUE (codigo_veiculo),
    CONSTRAINT uk_tb_veiculo_numero UNIQUE (numero_frota),
    CONSTRAINT uk_tb_veiculo_placa UNIQUE (placa),
    CONSTRAINT fk_tb_veiculo_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)
);

CREATE INDEX IF NOT EXISTS idx_tb_veiculo_id_empresa ON tb_veiculo (id_empresa);

CREATE TABLE IF NOT EXISTS tb_linha (
    id_linha         SERIAL       PRIMARY KEY,
    codigo_linha     INT          NOT NULL,
    id_empresa       INT          NOT NULL,
    descricao        VARCHAR(150) NOT NULL,
    id_local_origem  INT          NOT NULL,
    id_local_destino INT          NOT NULL,
    ativo            BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_linha_codigo UNIQUE (codigo_linha),
    CONSTRAINT fk_tb_linha_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_tb_linha_origem
        FOREIGN KEY (id_local_origem) REFERENCES tb_local (id_local),
    CONSTRAINT fk_tb_linha_destino
        FOREIGN KEY (id_local_destino) REFERENCES tb_local (id_local)
);

CREATE INDEX IF NOT EXISTS idx_tb_linha_id_empresa ON tb_linha (id_empresa);
CREATE INDEX IF NOT EXISTS idx_tb_linha_origem ON tb_linha (id_local_origem);
CREATE INDEX IF NOT EXISTS idx_tb_linha_destino ON tb_linha (id_local_destino);

CREATE TABLE IF NOT EXISTS tb_usuario (
    id_usuario      SERIAL       PRIMARY KEY,
    matricula       VARCHAR(20)  NOT NULL,
    nome            VARCHAR(150) NOT NULL,
    senha           VARCHAR(255) NOT NULL,
    id_perfil       INT          NOT NULL,
    id_empresa      INT          NULL,
    id_turno        INT          NULL,
    id_local        INT          NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    trocar_senha    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_tb_usuario_matricula UNIQUE (matricula),
    CONSTRAINT fk_tb_usuario_perfil
        FOREIGN KEY (id_perfil) REFERENCES tb_perfil (id_perfil),
    CONSTRAINT fk_tb_usuario_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_tb_usuario_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_usuario_local
        FOREIGN KEY (id_local) REFERENCES tb_local (id_local)
);

CREATE INDEX IF NOT EXISTS idx_tb_usuario_id_perfil ON tb_usuario (id_perfil);
CREATE INDEX IF NOT EXISTS idx_tb_usuario_id_empresa ON tb_usuario (id_empresa);
CREATE INDEX IF NOT EXISTS idx_tb_usuario_id_turno ON tb_usuario (id_turno);
CREATE INDEX IF NOT EXISTS idx_tb_usuario_id_local ON tb_usuario (id_local);
CREATE INDEX IF NOT EXISTS idx_tb_usuario_trocar_senha ON tb_usuario (trocar_senha);

INSERT INTO tb_perfil (codigo_perfil, descricao) VALUES
    (1, 'Administrador'),
    (2, 'Despachante'),
    (3, 'Inspetor')
ON CONFLICT (codigo_perfil) DO UPDATE SET descricao = EXCLUDED.descricao;

-- Administrador padrão — senha: 123 (bcrypt cost 12)
INSERT INTO tb_usuario (
    matricula, nome, senha, id_perfil,
    id_empresa, id_turno, id_local, ativo, trocar_senha
)
SELECT
    '59817',
    'Administrador',
    '$2b$12$8jysodvO61a4ZP/2LuE2fe1dyiQMtUsCrCn2ZwLluY1qyLMuzvO7S',
    p.id_perfil,
    NULL, NULL, NULL, TRUE, FALSE
FROM tb_perfil p
WHERE p.codigo_perfil = 1
ON CONFLICT (matricula) DO UPDATE SET
    nome = EXCLUDED.nome,
    senha = EXCLUDED.senha,
    id_perfil = EXCLUDED.id_perfil,
    id_empresa = EXCLUDED.id_empresa,
    id_turno = EXCLUDED.id_turno,
    id_local = EXCLUDED.id_local,
    ativo = EXCLUDED.ativo,
    trocar_senha = EXCLUDED.trocar_senha;

-- ---------------------------------------------------------------------------
-- Indicadores e configuração
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_indicador (
    id_ind     SERIAL       PRIMARY KEY,
    cod_ind    INT          NOT NULL,
    descricao  VARCHAR(20)  NOT NULL,
    detalhe    VARCHAR(120) NULL,
    CONSTRAINT uk_tb_indicador_cod_ind UNIQUE (cod_ind)
);

CREATE TABLE IF NOT EXISTS tb_ind_perf (
    id_indperf SERIAL PRIMARY KEY,
    id_ind     INT NOT NULL,
    id_perfil  INT NOT NULL,
    CONSTRAINT uk_tb_ind_perf_ind_perfil UNIQUE (id_ind, id_perfil),
    CONSTRAINT fk_tb_ind_perf_indicador
        FOREIGN KEY (id_ind) REFERENCES tb_indicador (id_ind),
    CONSTRAINT fk_tb_ind_perf_perfil
        FOREIGN KEY (id_perfil) REFERENCES tb_perfil (id_perfil)
);

CREATE INDEX IF NOT EXISTS idx_tb_ind_perf_id_ind ON tb_ind_perf (id_ind);
CREATE INDEX IF NOT EXISTS idx_tb_ind_perf_id_perfil ON tb_ind_perf (id_perfil);

CREATE TABLE IF NOT EXISTS tb_configuracao (
    idconf SERIAL      PRIMARY KEY,
    -- VARCHAR(32): chave 'QTD_MAX_TENTATIVAS' tem 18 chars (MariaDB VARCHAR(15)
    -- costuma truncar em modo não-strict; Postgres rejeita).
    chave  VARCHAR(32) NOT NULL,
    valor  VARCHAR(30) NOT NULL
);

INSERT INTO tb_configuracao (chave, valor)
SELECT 'QTD_MAX_TENTATIVAS', '3'
WHERE NOT EXISTS (
    SELECT 1 FROM tb_configuracao WHERE chave = 'QTD_MAX_TENTATIVAS'
);

-- ---------------------------------------------------------------------------
-- Guia / chegada-saída / avaria
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_guia (
    id_guia       SERIAL       PRIMARY KEY,
    numero        VARCHAR(15)  NULL,
    id_empresa    INT          NULL,
    id_linha      INT          NULL,
    id_turno      INT          NULL,
    id_veiculo    INT          NULL,
    id_motorista  INT          NULL,
    hor_ini       TIMESTAMP    NULL,
    hor_fim       TIMESTAMP    NULL,
    roleta01_ini  INT          NULL,
    roleta01_fim  INT          NULL,
    roleta2_ini   INT          NULL,
    roleta2_fim   INT          NULL,
    observacao    VARCHAR(150) NULL,
    data          TIMESTAMP    NULL,
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
);

CREATE INDEX IF NOT EXISTS idx_tb_guia_numero ON tb_guia (numero);
CREATE INDEX IF NOT EXISTS idx_tb_guia_empresa ON tb_guia (id_empresa);
CREATE INDEX IF NOT EXISTS idx_tb_guia_linha ON tb_guia (id_linha);
CREATE INDEX IF NOT EXISTS idx_tb_guia_turno ON tb_guia (id_turno);
CREATE INDEX IF NOT EXISTS idx_tb_guia_veiculo ON tb_guia (id_veiculo);
CREATE INDEX IF NOT EXISTS idx_tb_guia_motorista ON tb_guia (id_motorista);

CREATE TABLE IF NOT EXISTS tb_chegada_saida (
    id_cs          SERIAL      PRIMARY KEY,
    id_gui         INT         NULL,
    id_linha       INT         NULL,
    carro          INT         NULL,
    evento         VARCHAR(1)  NULL,
    horario        VARCHAR(5)  NULL,
    roleta_01      INT         NULL,
    roleta_02      INT         NULL,
    temperatura    INT         NULL,
    linha_destino  INT         NULL,
    destino        INT         NULL,
    CONSTRAINT fk_tb_chegada_saida_guia
        FOREIGN KEY (id_gui) REFERENCES tb_guia (id_guia),
    CONSTRAINT fk_tb_chegada_saida_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_chegada_saida_carro
        FOREIGN KEY (carro) REFERENCES tb_veiculo (id_veiculo)
);

CREATE INDEX IF NOT EXISTS idx_tb_chegada_saida_gui ON tb_chegada_saida (id_gui);
CREATE INDEX IF NOT EXISTS idx_tb_chegada_saida_linha ON tb_chegada_saida (id_linha);
CREATE INDEX IF NOT EXISTS idx_tb_chegada_saida_carro ON tb_chegada_saida (carro);
CREATE INDEX IF NOT EXISTS idx_tb_chegada_saida_evento ON tb_chegada_saida (evento);

CREATE TABLE IF NOT EXISTS tb_tip_avaria (
    id_tip    SERIAL      PRIMARY KEY,
    descricao VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_avaria (
    id_av      SERIAL      PRIMARY KEY,
    id_vei     INT         NOT NULL,
    id_tip     INT         NOT NULL,
    id_usuario INT         NOT NULL,
    data       TIMESTAMP   NOT NULL,
    texto      VARCHAR(500) NULL,
    CONSTRAINT fk_tb_avaria_veiculo
        FOREIGN KEY (id_vei) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_avaria_tip_avaria
        FOREIGN KEY (id_tip) REFERENCES tb_tip_avaria (id_tip),
    CONSTRAINT fk_tb_avaria_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
);

CREATE INDEX IF NOT EXISTS idx_tb_avaria_id_vei ON tb_avaria (id_vei);
CREATE INDEX IF NOT EXISTS idx_tb_avaria_id_tip ON tb_avaria (id_tip);
CREATE INDEX IF NOT EXISTS idx_tb_avaria_id_usuario ON tb_avaria (id_usuario);
CREATE INDEX IF NOT EXISTS idx_tb_avaria_data ON tb_avaria (data);

-- ---------------------------------------------------------------------------
-- MAPA operacional
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_map (
    id_registro         SERIAL       PRIMARY KEY,
    cod_map             INT          NOT NULL,
    id_usuario          INT          NOT NULL,
    id_linha            INT          NOT NULL,
    id_turno            INT          NOT NULL,
    data                DATE         NOT NULL,
    inicio_jornada_des  TIMESTAMP    NOT NULL,
    fim_jornada_des     TIMESTAMP    NULL,
    observacao          VARCHAR(500) NULL,
    CONSTRAINT uk_tb_map_cod_map UNIQUE (cod_map),
    CONSTRAINT fk_tb_map_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_tb_map_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_tb_map_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario)
);

CREATE INDEX IF NOT EXISTS idx_tb_map_usuario ON tb_map (id_usuario);
CREATE INDEX IF NOT EXISTS idx_tb_map_linha ON tb_map (id_linha);
CREATE INDEX IF NOT EXISTS idx_tb_map_turno ON tb_map (id_turno);
CREATE INDEX IF NOT EXISTS idx_tb_map_data ON tb_map (data);
CREATE INDEX IF NOT EXISTS idx_tb_map_inicio ON tb_map (inicio_jornada_des);

CREATE TABLE IF NOT EXISTS tb_item_map (
    id_item        SERIAL    PRIMARY KEY,
    idmap          INT       NOT NULL,
    id_veiculo     INT       NOT NULL,
    id_motorista   INT       NOT NULL,
    hor_ini_jor    TIMESTAMP NULL,
    hor_fim_jor    TIMESTAMP NULL,
    chegada_ponto  TIMESTAMP NULL,
    CONSTRAINT fk_tb_item_map_map
        FOREIGN KEY (idmap) REFERENCES tb_map (id_registro),
    CONSTRAINT fk_tb_item_map_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_tb_item_map_motorista
        FOREIGN KEY (id_motorista) REFERENCES tb_motorista (id_motorista)
);

CREATE INDEX IF NOT EXISTS idx_tb_item_map_idmap ON tb_item_map (idmap);
CREATE INDEX IF NOT EXISTS idx_tb_item_map_veiculo ON tb_item_map (id_veiculo);
CREATE INDEX IF NOT EXISTS idx_tb_item_map_motorista ON tb_item_map (id_motorista);

CREATE TABLE IF NOT EXISTS tb_viagem (
    id_viagem         SERIAL      PRIMARY KEY,
    id_item_registro  INT         NOT NULL,
    horario_chegada   TIMESTAMP   NOT NULL,
    placa             VARCHAR(5)  NULL,
    horario_saida     TIMESTAMP   NOT NULL,
    intervalo         INT         NULL,
    qtd_pas_ida       INT         NULL,
    qtd_pas_volta     INT         NULL,
    CONSTRAINT fk_tb_viagem_item_map
        FOREIGN KEY (id_item_registro) REFERENCES tb_item_map (id_item)
);

CREATE INDEX IF NOT EXISTS idx_tb_viagem_id_item_registro ON tb_viagem (id_item_registro);
