-- Migration P1: frota canônica C47/C30/D13 + revisão de legados
-- Idempotente. MariaDB. NÃO apaga dados.
-- Estratégia legado:
--   1) 5 dígitos 47/30/13xxx com id_empresa compatível → prefixa letra (C/D).
--   2) Demais formatos não canônicos → frota_status = PENDENTE_REVISAO_FROTA (sem conversão silenciosa).

USE map;

-- Coluna de status de revisão (nullable = OK / canônico)
SET @c := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_veiculo' AND COLUMN_NAME = 'frota_status'
);
SET @s := IF(@c = 0,
  'ALTER TABLE tb_veiculo ADD COLUMN frota_status VARCHAR(40) NULL COMMENT ''NULL=ok | PENDENTE_REVISAO_FROTA'' AFTER numero_frota',
  'DO 0');
PREPARE stmt FROM @s; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Atualiza regra em tb_configuracao (chave já alargada na Fase 0 lab; se curta, UPDATE parcial)
UPDATE tb_configuracao SET valor = '^(C47|C30|D13)[0-9]{3}$' WHERE chave = 'FROTA_REGEX';
UPDATE tb_configuracao SET valor = '6' WHERE chave = 'FROTA_MAX_LEN';
UPDATE tb_configuracao SET valor = 'C47654' WHERE chave = 'FROTA_EXEMPLO';

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_REGEX', '^(C47|C30|D13)[0-9]{3}$' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_REGEX');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_MAX_LEN', '6' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_MAX_LEN');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_EXEMPLO', 'C47654' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_EXEMPLO');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_MENSAGEM',
  'Informe um carro válido: C47xxx (Redentor), C30xxx (Futuro) ou D13xxx (Barra). Exemplos: C47654, C30114 ou D13450.'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_MENSAGEM');

-- Conversão segura: só 5 dígitos ambíguos-zero quando empresa bate com faixa
-- Futuro (descricao LIKE %Futuro% ou codigo 2): 30xxx → C30xxx
UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.id_empresa = v.id_empresa
SET v.numero_frota = CONCAT('C', UPPER(TRIM(v.numero_frota))),
    v.frota_status = NULL
WHERE v.numero_frota REGEXP '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '30%'
  AND (
    LOWER(e.descricao) LIKE '%futuro%'
    OR e.codigo_empresa = 2
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = CONCAT('C', UPPER(TRIM(v.numero_frota)))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Redentor: 47xxx → C47xxx
UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.id_empresa = v.id_empresa
SET v.numero_frota = CONCAT('C', UPPER(TRIM(v.numero_frota))),
    v.frota_status = NULL
WHERE v.numero_frota REGEXP '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '47%'
  AND (
    LOWER(e.descricao) LIKE '%redentor%'
    OR e.codigo_empresa = 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = CONCAT('C', UPPER(TRIM(v.numero_frota)))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Barra: 13xxx → D13xxx
UPDATE tb_veiculo v
INNER JOIN tb_empresa e ON e.id_empresa = v.id_empresa
SET v.numero_frota = CONCAT('D', UPPER(TRIM(v.numero_frota))),
    v.frota_status = NULL
WHERE v.numero_frota REGEXP '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '13%'
  AND (
    LOWER(e.descricao) LIKE '%barra%'
    OR e.codigo_empresa = 3
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = CONCAT('D', UPPER(TRIM(v.numero_frota)))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Já canônicos em minúsculas → maiúsculas
UPDATE tb_veiculo
SET numero_frota = UPPER(TRIM(numero_frota)),
    frota_status = NULL
WHERE numero_frota REGEXP '^[cCdD](47|30|13)[0-9]{3}$';

-- Legado ambíguo / incompatível: marcar revisão (não converte)
UPDATE tb_veiculo
SET frota_status = 'PENDENTE_REVISAO_FROTA'
WHERE frota_status IS NULL
  AND UPPER(TRIM(numero_frota)) NOT REGEXP '^(C47|C30|D13)[0-9]{3}$';
