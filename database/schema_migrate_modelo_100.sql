-- Recria todo o schema MAP no modelo normalizado (nomenclatura + tipos + 3FN)
USE map;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS tb_item_map;
DROP TABLE IF EXISTS tb_map;
DROP TABLE IF EXISTS tb_item_reg_ponto;
DROP TABLE IF EXISTS tb_reg_ponto;
DROP TABLE IF EXISTS tb_veiculo;
DROP TABLE IF EXISTS tb_iregp;
DROP TABLE IF EXISTS tb_regp;
DROP TABLE IF EXISTS tb_veic;
DROP TABLE IF EXISTS tb_linha;
DROP TABLE IF EXISTS tb_turno;
DROP TABLE IF EXISTS tb_motorista;
DROP TABLE IF EXISTS tb_local;
DROP TABLE IF EXISTS tb_empresa;
DROP TABLE IF EXISTS tb_usuario;
DROP TABLE IF EXISTS tb_perfil;

SET FOREIGN_KEY_CHECKS = 1;
