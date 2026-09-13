-- ----------------------------
-- Deus seja Louvado!
-- ----------------------------
-- Amplia tb_configuracao para chaves longas e mensagens de frota.
-- Espelho de schema_migrate_tb_configuracao_chave_valor_p2.sql
-- Idempotente em PostgreSQL.

ALTER TABLE tb_configuracao
    ALTER COLUMN chave TYPE VARCHAR(32);

ALTER TABLE tb_configuracao
    ALTER COLUMN valor TYPE VARCHAR(255);
