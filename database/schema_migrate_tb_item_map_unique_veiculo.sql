-- Impede o mesmo veículo duas vezes no mesmo MAPA
-- Pré-check (deve retornar 0 linhas):
-- SELECT idmap, id_veiculo, COUNT(*) AS qtd
-- FROM tb_item_map
-- GROUP BY idmap, id_veiculo
-- HAVING COUNT(*) > 1;

USE map;

ALTER TABLE tb_item_map
  ADD UNIQUE KEY uq_tb_item_map_idmap_veiculo (idmap, id_veiculo);
