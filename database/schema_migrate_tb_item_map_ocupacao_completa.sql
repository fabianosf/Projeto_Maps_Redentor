-- ============================================================
-- Migration idempotente: ocupação operacional em tb_item_map
-- Tabela real do alias `i` em GET /api/v1/mapas/ocupacao.
--
-- NÃO apaga/recria dados. Pode rodar múltiplas vezes.
-- Colunas novas ficam NULL (exceto status_escala com default).
-- Não inventa início/fim real nem duração para histórico.
-- ============================================================

USE map;

-- Helper pattern: ADD COLUMN only if missing

-- status_escala
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'status_escala'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN status_escala VARCHAR(20) NOT NULL DEFAULT ''EM_ANDAMENTO'' COMMENT ''EM_ANDAMENTO | ENCERRADA'' AFTER chegada_ponto',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- inicio_real (DATETIME — compatível com o backend; permite cruzar meia-noite)
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'inicio_real'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN inicio_real DATETIME NULL COMMENT ''Início real da escala'' AFTER chegada_ponto',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- fim_real
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'fim_real'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN fim_real DATETIME NULL COMMENT ''Fim real / data_hora_baixa'' AFTER inicio_real',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- baixa_em (compat — timestamp completo da baixa)
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'baixa_em'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN baixa_em DATETIME NULL COMMENT ''Data/hora da baixa operacional'' AFTER status_escala',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- data_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'data_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN data_baixa DATE NULL COMMENT ''Data da baixa (derivada de fim_real/baixa_em)'' AFTER baixa_em',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- hora_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'hora_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN hora_baixa TIME NULL COMMENT ''Hora da baixa (derivada de fim_real/baixa_em)'' AFTER data_baixa',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- motivo_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'motivo_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN motivo_baixa VARCHAR(30) NULL COMMENT ''Motivo operacional da baixa'' AFTER hora_baixa',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- observacao_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'observacao_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN observacao_baixa TEXT NULL COMMENT ''Observação da baixa'' AFTER motivo_baixa',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- duracao_trabalhada_minutos
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'duracao_trabalhada_minutos'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN duracao_trabalhada_minutos INT NULL COMMENT ''Minutos = fim_real - inicio_real'' AFTER observacao_baixa',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Itens legados: apenas status EM_ANDAMENTO (não inventar horários reais)
UPDATE tb_item_map
SET status_escala = 'EM_ANDAMENTO'
WHERE status_escala IS NULL
   OR TRIM(status_escala) = ''
   OR UPPER(TRIM(status_escala)) NOT IN ('EM_ANDAMENTO', 'ENCERRADA');

-- Compat: se já houver baixa_em e fim_real vazio em ENCERRADA, copiar (sem inventar)
UPDATE tb_item_map
SET fim_real = baixa_em
WHERE fim_real IS NULL
  AND baixa_em IS NOT NULL
  AND UPPER(TRIM(status_escala)) = 'ENCERRADA';

-- Preencher data_baixa/hora_baixa a partir de fim_real ou baixa_em quando vazios
UPDATE tb_item_map
SET
  data_baixa = COALESCE(data_baixa, DATE(COALESCE(fim_real, baixa_em))),
  hora_baixa = COALESCE(hora_baixa, TIME(COALESCE(fim_real, baixa_em)))
WHERE UPPER(TRIM(status_escala)) = 'ENCERRADA'
  AND COALESCE(fim_real, baixa_em) IS NOT NULL
  AND (data_baixa IS NULL OR hora_baixa IS NULL);

-- Remover UNIQUE (idmap, id_veiculo) se existir — permite reuso após baixa
SET @uq := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'uq_tb_item_map_idmap_veiculo'
);
SET @s := IF(@uq > 0,
  'ALTER TABLE tb_item_map DROP INDEX uq_tb_item_map_idmap_veiculo',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índices de ocupação
SET @i := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_status_escala'
);
SET @s := IF(@i = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_status_escala (status_escala)',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @i := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_veiculo_status'
);
SET @s := IF(@i = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_veiculo_status (id_veiculo, status_escala)',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @i := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_motorista_status'
);
SET @s := IF(@i = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_motorista_status (id_motorista, status_escala)',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;
