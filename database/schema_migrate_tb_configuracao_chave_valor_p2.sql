-- ----------------------------
-- Deus seja Louvado!
-- ----------------------------
-- Amplia tb_configuracao para chaves longas (QTD_MAX_TENTATIVAS, BLOQUEIO_*)
-- e valores de mensagem de frota.
-- Idempotente em MariaDB 10.4+.

ALTER TABLE tb_configuracao
  MODIFY COLUMN chave VARCHAR(32) NOT NULL COMMENT 'Código da chave',
  MODIFY COLUMN valor VARCHAR(255) NOT NULL COMMENT 'Valor da chave';
