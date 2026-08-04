-- Migração local: FKs passam a apontar para PKs (id*)
-- ATENÇÃO: recria as tabelas do banco map (dados de seed serão restaurados em seguida)
-- Executar como root

USE map;

SET FOREIGN_KEY_CHECKS = 0;

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
