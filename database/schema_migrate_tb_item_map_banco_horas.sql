-- Banco de horas operacional: início/fim reais e duração na escala (item MAPA).
-- Preserva horários planejados (hor_ini_jor / hor_fim_jor / chegada_ponto).
-- Não inventa horários reais para registros históricos.

USE map;

-- inicio_real
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'inicio_real'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN inicio_real DATETIME NULL COMMENT ''Início real da escala'' AFTER chegada_ponto',
  'SELECT 1');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- fim_real
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'fim_real'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN fim_real DATETIME NULL COMMENT ''Fim real / data_hora_baixa'' AFTER inicio_real',
  'SELECT 1');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- motivo_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'motivo_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN motivo_baixa VARCHAR(120) NULL COMMENT ''Motivo operacional da baixa'' AFTER baixa_em',
  'SELECT 1');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- observacao_baixa
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'observacao_baixa'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN observacao_baixa VARCHAR(500) NULL COMMENT ''Observação da baixa'' AFTER motivo_baixa',
  'SELECT 1');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- duracao_trabalhada_minutos
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_item_map' AND COLUMN_NAME = 'duracao_trabalhada_minutos'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_item_map ADD COLUMN duracao_trabalhada_minutos INT NULL COMMENT ''Minutos = fim_real - inicio_real'' AFTER observacao_baixa',
  'SELECT 1');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Compatibilidade: copiar baixa_em → fim_real quando já houver baixa sem fim_real
UPDATE tb_item_map
SET fim_real = baixa_em
WHERE fim_real IS NULL
  AND baixa_em IS NOT NULL
  AND UPPER(TRIM(status_escala)) = 'ENCERRADA';
