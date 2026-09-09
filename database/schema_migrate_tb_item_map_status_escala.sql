-- Status operacional da escala (item MAPA) + baixa.
-- EM_ANDAMENTO: ocupa veículo e motorista globalmente.
-- ENCERRADA: libera ambos; histórico e viagens permanecem.
--
-- Remove UNIQUE (idmap, id_veiculo) para permitir reutilizar o mesmo
-- veículo no mesmo MAPA após a baixa (nova escala).

USE map;

-- 1) Colunas de status / baixa
SET @col_status := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND COLUMN_NAME = 'status_escala'
);
SET @sql_status := IF(
  @col_status = 0,
  'ALTER TABLE tb_item_map ADD COLUMN status_escala VARCHAR(20) NOT NULL DEFAULT ''EM_ANDAMENTO'' COMMENT ''EM_ANDAMENTO | ENCERRADA'' AFTER chegada_ponto',
  'SELECT 1'
);
PREPARE stmt FROM @sql_status;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_baixa := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND COLUMN_NAME = 'baixa_em'
);
SET @sql_baixa := IF(
  @col_baixa = 0,
  'ALTER TABLE tb_item_map ADD COLUMN baixa_em DATETIME NULL COMMENT ''Data/hora da baixa operacional'' AFTER status_escala',
  'SELECT 1'
);
PREPARE stmt FROM @sql_baixa;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) Itens legados → EM_ANDAMENTO
UPDATE tb_item_map
SET status_escala = 'EM_ANDAMENTO'
WHERE status_escala IS NULL
   OR TRIM(status_escala) = ''
   OR UPPER(status_escala) NOT IN ('EM_ANDAMENTO', 'ENCERRADA');

-- 3) Remover UNIQUE (idmap, id_veiculo) se existir
SET @uq := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'uq_tb_item_map_idmap_veiculo'
);
SET @sql_drop_uq := IF(
  @uq > 0,
  'ALTER TABLE tb_item_map DROP INDEX uq_tb_item_map_idmap_veiculo',
  'SELECT 1'
);
PREPARE stmt FROM @sql_drop_uq;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4) Índices de consulta de ocupação
SET @idx_st := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_status_escala'
);
SET @sql_idx_st := IF(
  @idx_st = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_status_escala (status_escala)',
  'SELECT 1'
);
PREPARE stmt FROM @sql_idx_st;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_vs := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_veiculo_status'
);
SET @sql_idx_vs := IF(
  @idx_vs = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_veiculo_status (id_veiculo, status_escala)',
  'SELECT 1'
);
PREPARE stmt FROM @sql_idx_vs;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_ms := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tb_item_map'
    AND INDEX_NAME = 'idx_tb_item_map_motorista_status'
);
SET @sql_idx_ms := IF(
  @idx_ms = 0,
  'ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_motorista_status (id_motorista, status_escala)',
  'SELECT 1'
);
PREPARE stmt FROM @sql_idx_ms;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
