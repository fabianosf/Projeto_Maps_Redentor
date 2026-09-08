-- Motorista opcional no item (preenchido no detalhe do MAPA)
USE map;

ALTER TABLE tb_item_map
  MODIFY id_motorista INT NULL COMMENT 'FK tb_motorista — opcional no cadastro inicial';
