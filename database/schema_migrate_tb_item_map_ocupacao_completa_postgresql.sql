-- ============================================================
-- Migration PostgreSQL idempotente: ocupação / status / baixa /
-- horários reais / banco de horas em tb_item_map
-- Espelho funcional de:
--   schema_migrate_tb_item_map_ocupacao_completa.sql
--   schema_migrate_tb_item_map_status_escala.sql
--   schema_migrate_tb_item_map_banco_horas.sql
--   schema_migrate_tb_item_map_motorista_null.sql
--
-- NÃO apaga/recria/trunca dados. Pode rodar múltiplas vezes.
-- Sem blocos DO $$ (aplicador divide por ';').
-- ============================================================

-- Motorista opcional no cadastro inicial da escala
ALTER TABLE tb_item_map
    ALTER COLUMN id_motorista DROP NOT NULL;

-- status_escala
ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS status_escala VARCHAR(20) NOT NULL DEFAULT 'EM_ANDAMENTO';

-- Horários reais (TIMESTAMP — cruzar meia-noite)
ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS inicio_real TIMESTAMP NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS fim_real TIMESTAMP NULL;

-- Baixa operacional
ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS baixa_em TIMESTAMP NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS data_baixa DATE NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS hora_baixa TIME NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS motivo_baixa VARCHAR(120) NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS observacao_baixa TEXT NULL;

ALTER TABLE tb_item_map
    ADD COLUMN IF NOT EXISTS duracao_trabalhada_minutos INT NULL;

-- Legados: apenas status EM_ANDAMENTO (não inventar horários reais)
UPDATE tb_item_map
SET status_escala = 'EM_ANDAMENTO'
WHERE status_escala IS NULL
   OR TRIM(status_escala) = ''
   OR UPPER(TRIM(status_escala)) NOT IN ('EM_ANDAMENTO', 'ENCERRADA');

-- Compat: copiar baixa_em → fim_real quando ENCERRADA sem fim_real
UPDATE tb_item_map
SET fim_real = baixa_em
WHERE fim_real IS NULL
  AND baixa_em IS NOT NULL
  AND UPPER(TRIM(status_escala)) = 'ENCERRADA';

-- Preencher data_baixa/hora_baixa a partir de fim_real ou baixa_em
UPDATE tb_item_map
SET
  data_baixa = COALESCE(data_baixa, CAST(COALESCE(fim_real, baixa_em) AS date)),
  hora_baixa = COALESCE(hora_baixa, CAST(COALESCE(fim_real, baixa_em) AS time))
WHERE UPPER(TRIM(status_escala)) = 'ENCERRADA'
  AND COALESCE(fim_real, baixa_em) IS NOT NULL
  AND (data_baixa IS NULL OR hora_baixa IS NULL);

-- Remover UNIQUE (idmap, id_veiculo) se existir — permite reuso após baixa
DROP INDEX IF EXISTS uq_tb_item_map_idmap_veiculo;

-- Índices de ocupação
CREATE INDEX IF NOT EXISTS idx_tb_item_map_status_escala
    ON tb_item_map (status_escala);

CREATE INDEX IF NOT EXISTS idx_tb_item_map_veiculo_status
    ON tb_item_map (id_veiculo, status_escala);

CREATE INDEX IF NOT EXISTS idx_tb_item_map_motorista_status
    ON tb_item_map (id_motorista, status_escala);
