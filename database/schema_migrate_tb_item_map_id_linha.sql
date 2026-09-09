-- Fase schema: linha por item do MAPA; cabeçalho id_linha transitório nullable.
-- UP / DOWN documentados neste arquivo.

USE map;

-- ========== UP ==========

ALTER TABLE tb_item_map
  ADD COLUMN id_linha INT NULL COMMENT 'FK tb_linha — empresa via linha'
  AFTER idmap;

UPDATE tb_item_map i
INNER JOIN tb_map m ON m.id_registro = i.idmap
SET i.id_linha = m.id_linha
WHERE i.id_linha IS NULL
  AND m.id_linha IS NOT NULL;

-- Validação recomendada antes do NOT NULL:
-- SELECT COUNT(*) FROM tb_item_map WHERE id_linha IS NULL;

ALTER TABLE tb_item_map
  ADD KEY idx_tb_item_map_id_linha (id_linha),
  ADD CONSTRAINT fk_tb_item_map_linha
    FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha);

ALTER TABLE tb_item_map
  MODIFY id_linha INT NOT NULL COMMENT 'FK tb_linha — empresa via linha';

ALTER TABLE tb_map
  MODIFY id_linha INT NULL COMMENT 'Legado — preferir tb_item_map.id_linha';

-- ========== DOWN (reversível) ==========
-- Pré-condição: recuperar id_linha do 1º item onde header estiver NULL.
/*
UPDATE tb_map m
SET m.id_linha = (
  SELECT i.id_linha FROM tb_item_map i
  WHERE i.idmap = m.id_registro
  ORDER BY i.id_item
  LIMIT 1
)
WHERE m.id_linha IS NULL;

-- Falhar se ainda houver NULL:
-- SELECT COUNT(*) FROM tb_map WHERE id_linha IS NULL;

ALTER TABLE tb_map
  MODIFY id_linha INT NOT NULL COMMENT 'FK tb_linha.id_linha';

ALTER TABLE tb_item_map
  DROP FOREIGN KEY fk_tb_item_map_linha,
  DROP KEY idx_tb_item_map_id_linha,
  DROP COLUMN id_linha;
*/
