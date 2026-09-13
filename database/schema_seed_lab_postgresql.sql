-- Seed mínimo de laboratório local (PostgreSQL) — idempotente.
-- Empresas / turnos / locais / linhas / veículos / motoristas para smoke.
-- NÃO trunca nem apaga dados existentes.

INSERT INTO tb_empresa (codigo_empresa, descricao, prefixo_mapa, ativo)
SELECT 1, 'Redentor', 'Red', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_empresa WHERE codigo_empresa = 1);

INSERT INTO tb_empresa (codigo_empresa, descricao, prefixo_mapa, ativo)
SELECT 2, 'Futuro', 'Fut', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_empresa WHERE codigo_empresa = 2);

INSERT INTO tb_empresa (codigo_empresa, descricao, prefixo_mapa, ativo)
SELECT 3, 'Barra', 'Bar', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_empresa WHERE codigo_empresa = 3);

UPDATE tb_empresa SET prefixo_mapa = 'Red'
WHERE codigo_empresa = 1 AND (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '');
UPDATE tb_empresa SET prefixo_mapa = 'Fut'
WHERE codigo_empresa = 2 AND (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '');
UPDATE tb_empresa SET prefixo_mapa = 'Bar'
WHERE codigo_empresa = 3 AND (prefixo_mapa IS NULL OR TRIM(prefixo_mapa) = '');

INSERT INTO tb_turno (codigo_turno, descricao, ativo)
SELECT 1, 'TURNO 01', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_turno WHERE codigo_turno = 1);

INSERT INTO tb_turno (codigo_turno, descricao, ativo)
SELECT 2, 'TURNO 02', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_turno WHERE codigo_turno = 2);

INSERT INTO tb_turno (codigo_turno, descricao, ativo)
SELECT 3, 'TURNO 03', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_turno WHERE codigo_turno = 3);

INSERT INTO tb_local (codigo_local, descricao, ativo)
SELECT 37, 'Cidade De Deus', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_local WHERE codigo_local = 37);

INSERT INTO tb_local (codigo_local, descricao, ativo)
SELECT 31, 'Gavea', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_local WHERE codigo_local = 31);

INSERT INTO tb_local (codigo_local, descricao, ativo)
SELECT 42, 'Tanque', TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_local WHERE codigo_local = 42);

INSERT INTO tb_linha (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino, ativo)
SELECT 2,
       (SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = 1 LIMIT 1),
       'Tanque - Gavea',
       (SELECT id_local FROM tb_local WHERE codigo_local = 42 LIMIT 1),
       (SELECT id_local FROM tb_local WHERE codigo_local = 31 LIMIT 1),
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_linha WHERE codigo_linha = 2);

INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, id_empresa, ativo)
SELECT 47654, 'C47654', 'ABC1D23',
       (SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = 1 LIMIT 1),
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_veiculo WHERE UPPER(TRIM(numero_frota)) = 'C47654');

INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, id_empresa, ativo)
SELECT 30114, 'C30114', 'DEF4G56',
       (SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = 2 LIMIT 1),
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM tb_veiculo WHERE UPPER(TRIM(numero_frota)) = 'C30114');

INSERT INTO tb_motorista (matricula, nome, ativo) VALUES
    ('TESTE001', 'motorista_01', TRUE),
    ('TESTE002', 'motorista_02', TRUE),
    ('TESTE003', 'motorista_03', TRUE)
ON CONFLICT (matricula) DO UPDATE
SET nome = EXCLUDED.nome, ativo = TRUE;

INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq)
SELECT e.id_empresa, 0
FROM tb_empresa e
WHERE e.prefixo_mapa IS NOT NULL
  AND TRIM(e.prefixo_mapa) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM tb_mapa_seq s WHERE s.id_empresa = e.id_empresa
  );
