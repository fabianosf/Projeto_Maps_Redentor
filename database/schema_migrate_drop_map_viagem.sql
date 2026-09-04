-- Migração: remove tb_viagem, tb_item_map e tb_map
USE map;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS tb_viagem;
DROP TABLE IF EXISTS tb_item_map;
DROP TABLE IF EXISTS tb_map;

SET FOREIGN_KEY_CHECKS = 1;
