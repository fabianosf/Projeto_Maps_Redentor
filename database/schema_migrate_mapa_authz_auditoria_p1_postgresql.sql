-- Migration P1 PostgreSQL: responsabilidade de MAPA + leitura + auditoria
-- Espelho de schema_migrate_mapa_authz_auditoria_p1.sql
-- Idempotente. NÃO apaga dados. Sem blocos DO $$.

-- Responsável operacional do MAPA (despachante atribuído); default = criador
ALTER TABLE tb_map
    ADD COLUMN IF NOT EXISTS id_responsavel INT NULL;

UPDATE tb_map SET id_responsavel = id_usuario WHERE id_responsavel IS NULL;

CREATE INDEX IF NOT EXISTS idx_tb_map_id_responsavel ON tb_map (id_responsavel);

-- FK: aplicador ignora "already exists" se rodar de novo
ALTER TABLE tb_map
    ADD CONSTRAINT fk_tb_map_responsavel
    FOREIGN KEY (id_responsavel) REFERENCES tb_usuario (id_usuario);

-- Flag de leitura de MAPAs de outros (Despachante)
ALTER TABLE tb_usuario
    ADD COLUMN IF NOT EXISTS permite_leitura_mapas_outros BOOLEAN NOT NULL DEFAULT FALSE;

-- Cadastro excepcional ERP
ALTER TABLE tb_usuario
    ADD COLUMN IF NOT EXISTS pendente_validacao_erp BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE tb_usuario
    ADD COLUMN IF NOT EXISTS ticket_aprovacao_erp VARCHAR(80) NULL;

-- Auditoria imutável (APPEND-ONLY — sem UPDATE/DELETE na aplicação)
CREATE TABLE IF NOT EXISTS tb_auditoria (
    id_auditoria      BIGSERIAL    PRIMARY KEY,
    entidade          VARCHAR(60)  NOT NULL,
    id_entidade       VARCHAR(60)  NULL,
    acao              VARCHAR(60)  NOT NULL,
    id_executor       INT          NULL,
    perfil_executor   INT          NULL,
    criado_em         TIMESTAMP(3) NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    tz                VARCHAR(40)  NOT NULL DEFAULT 'America/Sao_Paulo',
    correlation_id    VARCHAR(64)  NULL,
    origem_ip         VARCHAR(64)  NULL,
    valores_antes     JSONB        NULL,
    valores_depois    JSONB        NULL,
    motivo            VARCHAR(500) NULL
);

CREATE INDEX IF NOT EXISTS idx_tb_auditoria_entidade
    ON tb_auditoria (entidade, id_entidade);

CREATE INDEX IF NOT EXISTS idx_tb_auditoria_executor
    ON tb_auditoria (id_executor);

CREATE INDEX IF NOT EXISTS idx_tb_auditoria_criado
    ON tb_auditoria (criado_em);
