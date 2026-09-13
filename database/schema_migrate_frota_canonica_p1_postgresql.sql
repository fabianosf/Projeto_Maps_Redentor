-- Migration P1 PostgreSQL: frota canônica C47/C30/D13 + revisão de legados
-- Espelho de schema_migrate_frota_canonica_p1.sql
-- Idempotente. NÃO apaga dados. REGEXP MariaDB → operador ~ do PostgreSQL.

ALTER TABLE tb_veiculo
    ADD COLUMN IF NOT EXISTS frota_status VARCHAR(40) NULL;

-- Atualiza / insere regras em tb_configuracao
UPDATE tb_configuracao SET valor = '^(C47|C30|D13)[0-9]{3}$' WHERE chave = 'FROTA_REGEX';
UPDATE tb_configuracao SET valor = '6' WHERE chave = 'FROTA_MAX_LEN';
UPDATE tb_configuracao SET valor = 'C47654' WHERE chave = 'FROTA_EXEMPLO';

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_REGEX', '^(C47|C30|D13)[0-9]{3}$'
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_REGEX');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_MAX_LEN', '6'
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_MAX_LEN');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_EXEMPLO', 'C47654'
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_EXEMPLO');

INSERT INTO tb_configuracao (chave, valor)
SELECT 'FROTA_MENSAGEM',
  'Informe um carro válido: C47xxx (Redentor), C30xxx (Futuro) ou D13xxx (Barra). Exemplos: C47654, C30114 ou D13450.'
WHERE NOT EXISTS (SELECT 1 FROM tb_configuracao WHERE chave = 'FROTA_MENSAGEM');

-- Conversão segura: só 5 dígitos quando empresa bate com faixa
-- Futuro: 30xxx → C30xxx
UPDATE tb_veiculo v
SET numero_frota = 'C' || UPPER(TRIM(v.numero_frota)),
    frota_status = NULL
FROM tb_empresa e
WHERE e.id_empresa = v.id_empresa
  AND v.numero_frota ~ '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '30%'
  AND (
    LOWER(e.descricao) LIKE '%futuro%'
    OR e.codigo_empresa = 2
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = 'C' || UPPER(TRIM(v.numero_frota))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Redentor: 47xxx → C47xxx
UPDATE tb_veiculo v
SET numero_frota = 'C' || UPPER(TRIM(v.numero_frota)),
    frota_status = NULL
FROM tb_empresa e
WHERE e.id_empresa = v.id_empresa
  AND v.numero_frota ~ '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '47%'
  AND (
    LOWER(e.descricao) LIKE '%redentor%'
    OR e.codigo_empresa = 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = 'C' || UPPER(TRIM(v.numero_frota))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Barra: 13xxx → D13xxx
UPDATE tb_veiculo v
SET numero_frota = 'D' || UPPER(TRIM(v.numero_frota)),
    frota_status = NULL
FROM tb_empresa e
WHERE e.id_empresa = v.id_empresa
  AND v.numero_frota ~ '^[0-9]{5}$'
  AND UPPER(TRIM(v.numero_frota)) LIKE '13%'
  AND (
    LOWER(e.descricao) LIKE '%barra%'
    OR e.codigo_empresa = 3
  )
  AND NOT EXISTS (
    SELECT 1 FROM tb_veiculo x
    WHERE UPPER(TRIM(x.numero_frota)) = 'D' || UPPER(TRIM(v.numero_frota))
      AND x.id_veiculo <> v.id_veiculo
  );

-- Já canônicos em minúsculas → maiúsculas
UPDATE tb_veiculo
SET numero_frota = UPPER(TRIM(numero_frota)),
    frota_status = NULL
WHERE numero_frota ~* '^[cd](47|30|13)[0-9]{3}$';

-- Legado ambíguo / incompatível: marcar revisão (não converte)
UPDATE tb_veiculo
SET frota_status = 'PENDENTE_REVISAO_FROTA'
WHERE frota_status IS NULL
  AND UPPER(TRIM(numero_frota)) !~ '^(C47|C30|D13)[0-9]{3}$';
