-- MariaDB: vincula veículo à empresa (filtro de frota por MAPA)
-- Legado: id_empresa NULL permitido; novos inserts via API exigem id_empresa.
USE map;

-- Coluna (idempotente via procedure simples)
SET @col_exists := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_veiculo'
      AND COLUMN_NAME = 'id_empresa'
);

SET @sql := IF(
    @col_exists = 0,
    'ALTER TABLE tb_veiculo ADD COLUMN id_empresa INT NULL COMMENT ''FK tb_empresa.id_empresa'' AFTER ativo',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Índice
SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_veiculo'
      AND INDEX_NAME = 'idx_tb_veiculo_id_empresa'
);

SET @sql := IF(
    @idx_exists = 0,
    'ALTER TABLE tb_veiculo ADD KEY idx_tb_veiculo_id_empresa (id_empresa)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- FK
SET @fk_exists := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_veiculo'
      AND CONSTRAINT_NAME = 'fk_tb_veiculo_empresa'
      AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);

SET @sql := IF(
    @fk_exists = 0,
    'ALTER TABLE tb_veiculo ADD CONSTRAINT fk_tb_veiculo_empresa FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Popular por match confiável: numero_frota / codigo_veiculo = dígitos do Prefixo CSV
-- (sem match → permanece NULL). Ex.: C30346 → codigo 30346.
-- Atualização via JOIN com staging não aplicada aqui; script Python opcional.
-- Inferência por faixa atual do app (somente se codigo_veiculo na faixa):
UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.descricao = 'Futuro' AND e.ativo = 1
SET v.id_empresa = e.id_empresa
WHERE v.id_empresa IS NULL
  AND v.codigo_veiculo BETWEEN 30000 AND 30999;

UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.descricao = 'Redentor' AND e.ativo = 1
SET v.id_empresa = e.id_empresa
WHERE v.id_empresa IS NULL
  AND v.codigo_veiculo BETWEEN 40000 AND 40999;

UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.descricao = 'Barra' AND e.ativo = 1
SET v.id_empresa = e.id_empresa
WHERE v.id_empresa IS NULL
  AND v.codigo_veiculo BETWEEN 13000 AND 13999;
