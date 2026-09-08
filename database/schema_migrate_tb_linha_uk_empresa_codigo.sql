-- UNIQUE de linha passa a ser por empresa + código (não só codigo_linha global)
USE map;

ALTER TABLE tb_linha DROP INDEX uk_tb_linha_codigo;

ALTER TABLE tb_linha
  ADD UNIQUE KEY uk_tb_linha_empresa_codigo (id_empresa, codigo_linha);
