-- Migration P1: responsabilidade de MAPA + leitura + auditoria imutável
-- Idempotente. MariaDB. NÃO apaga dados.

USE map;

-- Responsável operacional do MAPA (despachante atribuído); default = criador
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_map' AND COLUMN_NAME = 'id_responsavel'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_map ADD COLUMN id_responsavel INT NULL COMMENT ''FK tb_usuario — operador atribuído'' AFTER id_usuario',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE tb_map SET id_responsavel = id_usuario WHERE id_responsavel IS NULL;

SET @fk := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_map' AND CONSTRAINT_NAME = 'fk_tb_map_responsavel'
);
SET @s := IF(@fk = 0,
  'ALTER TABLE tb_map ADD CONSTRAINT fk_tb_map_responsavel FOREIGN KEY (id_responsavel) REFERENCES tb_usuario (id_usuario)',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_map' AND INDEX_NAME = 'idx_tb_map_id_responsavel'
);
SET @s := IF(@idx = 0,
  'ALTER TABLE tb_map ADD KEY idx_tb_map_id_responsavel (id_responsavel)',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Flag de leitura de MAPAs de outros (Despachante)
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'permite_leitura_mapas_outros'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_usuario ADD COLUMN permite_leitura_mapas_outros TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''1=despachante pode ler MAPAs de outros'' AFTER ativo',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Cadastro excepcional ERP
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'pendente_validacao_erp'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_usuario ADD COLUMN pendente_validacao_erp TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''1=cadastro temporário aguardando ERP'' AFTER permite_leitura_mapas_outros',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_usuario' AND COLUMN_NAME = 'ticket_aprovacao_erp'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_usuario ADD COLUMN ticket_aprovacao_erp VARCHAR(80) NULL COMMENT ''Ticket/aprovação do cadastro excepcional'' AFTER pendente_validacao_erp',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Auditoria imutável (APPEND-ONLY — sem UPDATE/DELETE na aplicação)
CREATE TABLE IF NOT EXISTS tb_auditoria (
    id_auditoria      BIGINT       NOT NULL AUTO_INCREMENT,
    entidade          VARCHAR(60)  NOT NULL COMMENT 'mapa|escala|viagem|usuario|acesso|...',
    id_entidade       VARCHAR(60)  NULL,
    acao              VARCHAR(60)  NOT NULL COMMENT 'criar|editar|baixa|excluir|transferir|corrigir|acesso_negado|...',
    id_executor       INT          NULL,
    perfil_executor   INT          NULL,
    criado_em         DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    tz                VARCHAR(40)  NOT NULL DEFAULT 'America/Sao_Paulo',
    correlation_id    VARCHAR(64)  NULL,
    origem_ip         VARCHAR(64)  NULL,
    valores_antes     JSON         NULL,
    valores_depois    JSON         NULL,
    motivo            VARCHAR(500) NULL,
    PRIMARY KEY (id_auditoria),
    KEY idx_tb_auditoria_entidade (entidade, id_entidade),
    KEY idx_tb_auditoria_executor (id_executor),
    KEY idx_tb_auditoria_criado (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
