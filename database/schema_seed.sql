-- Dados de exemplo coerentes — FKs por PK, modelo normalizado
USE map;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE tb_viagem;
TRUNCATE TABLE tb_item_map;
TRUNCATE TABLE tb_map;
TRUNCATE TABLE tb_veiculo;
TRUNCATE TABLE tb_linha;
TRUNCATE TABLE tb_turno;
TRUNCATE TABLE tb_motorista;
TRUNCATE TABLE tb_local;
TRUNCATE TABLE tb_empresa;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO tb_empresa (codigo_empresa, descricao) VALUES
    (1, 'Futuro'),
    (2, 'Redentor'),
    (3, 'Barra');

INSERT INTO tb_local (codigo_local, descricao) VALUES
    (10, 'Terminal Norte'),
    (20, 'Terminal Sul'),
    (30, 'Garagem Central'),
    (40, 'Ponto A'),
    (50, 'Ponto B');

INSERT INTO tb_motorista (matricula, nome) VALUES
    ('90001', 'Motorista Teste 01'),
    ('90002', 'Motorista Teste 02'),
    ('90003', 'Motorista Teste 03'),
    ('90004', 'Motorista Teste 04');

INSERT INTO tb_turno (codigo_turno, descricao) VALUES
    (1, 'TURNO 01'),
    (2, 'TURNO 02'),
    (3, 'TURNO 03');

INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa) VALUES
    (501, 'V-101', 'ABC1D23'),
    (502, 'V-102', 'EFG4H56'),
    (503, 'V-203', 'IJK7L89'),
    (504, 'V-304', 'MNO0P12');

INSERT INTO tb_linha (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino)
SELECT 101, e.id_empresa, 'Linha 101 Norte-Sul', lo.id_local, ld.id_local
FROM tb_empresa e
JOIN tb_local lo ON lo.codigo_local = 10
JOIN tb_local ld ON ld.codigo_local = 20
WHERE e.codigo_empresa = 1;

INSERT INTO tb_linha (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino)
SELECT 202, e.id_empresa, 'Linha 202 Sul-Central', lo.id_local, ld.id_local
FROM tb_empresa e
JOIN tb_local lo ON lo.codigo_local = 20
JOIN tb_local ld ON ld.codigo_local = 30
WHERE e.codigo_empresa = 2;

INSERT INTO tb_linha (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino)
SELECT 303, e.id_empresa, 'Linha 303 Central-A', lo.id_local, ld.id_local
FROM tb_empresa e
JOIN tb_local lo ON lo.codigo_local = 30
JOIN tb_local ld ON ld.codigo_local = 40
WHERE e.codigo_empresa = 2;

INSERT INTO tb_linha (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino)
SELECT 404, e.id_empresa, 'Linha 404 B-Norte', lo.id_local, ld.id_local
FROM tb_empresa e
JOIN tb_local lo ON lo.codigo_local = 50
JOIN tb_local ld ON ld.codigo_local = 10
WHERE e.codigo_empresa = 3;

INSERT INTO tb_map (
    cod_map, id_usuario, id_linha, id_turno,
    data, inicio_jornada_des, fim_jornada_des, observacao
)
SELECT 1001, u.id_usuario, li.id_linha, t.id_turno,
       '2026-07-08', '2026-07-08 06:00:00', '2026-07-08 14:00:00', NULL
FROM tb_usuario u
JOIN tb_linha li ON li.codigo_linha = 101
JOIN tb_turno t ON t.codigo_turno = 1
WHERE u.matricula = '1001';

INSERT INTO tb_map (
    cod_map, id_usuario, id_linha, id_turno,
    data, inicio_jornada_des, fim_jornada_des, observacao
)
SELECT 1002, u.id_usuario, li.id_linha, t.id_turno,
       '2026-07-08', '2026-07-08 14:00:00', '2026-07-08 22:00:00', 'Turno da tarde'
FROM tb_usuario u
JOIN tb_linha li ON li.codigo_linha = 101
JOIN tb_turno t ON t.codigo_turno = 2
WHERE u.matricula = '1002';

INSERT INTO tb_map (
    cod_map, id_usuario, id_linha, id_turno,
    data, inicio_jornada_des, fim_jornada_des, observacao
)
SELECT 1003, u.id_usuario, li.id_linha, t.id_turno,
       '2026-07-09', '2026-07-09 05:30:00', '2026-07-09 13:30:00', NULL
FROM tb_usuario u
JOIN tb_linha li ON li.codigo_linha = 202
JOIN tb_turno t ON t.codigo_turno = 1
WHERE u.matricula = '1001';

INSERT INTO tb_map (
    cod_map, id_usuario, id_linha, id_turno,
    data, inicio_jornada_des, fim_jornada_des, observacao
)
SELECT 1004, u.id_usuario, li.id_linha, t.id_turno,
       '2026-07-09', '2026-07-09 13:00:00', '2026-07-09 21:00:00', NULL
FROM tb_usuario u
JOIN tb_linha li ON li.codigo_linha = 303
JOIN tb_turno t ON t.codigo_turno = 2
WHERE u.matricula = '1002';

-- Jornada noturna cruzando meia-noite (DATETIME)
INSERT INTO tb_map (
    cod_map, id_usuario, id_linha, id_turno,
    data, inicio_jornada_des, fim_jornada_des, observacao
)
SELECT 1005, u.id_usuario, li.id_linha, t.id_turno,
       '2026-07-09', '2026-07-09 22:00:00', '2026-07-10 06:00:00', 'Jornada noturna'
FROM tb_usuario u
JOIN tb_linha li ON li.codigo_linha = 404
JOIN tb_turno t ON t.codigo_turno = 3
WHERE u.matricula = '1001';

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-08 06:00:00', '2026-07-08 14:00:00', '2026-07-08 06:45:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 501
JOIN tb_motorista m ON m.matricula = '90001'
WHERE r.cod_map = 1001;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-08 06:50:00', '2026-07-08 14:00:00', '2026-07-08 07:30:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 501
JOIN tb_motorista m ON m.matricula = '90001'
WHERE r.cod_map = 1001;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-08 14:00:00', '2026-07-08 22:00:00', '2026-07-08 14:55:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 502
JOIN tb_motorista m ON m.matricula = '90002'
WHERE r.cod_map = 1002;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-08 15:00:00', '2026-07-08 22:00:00', '2026-07-08 15:40:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 502
JOIN tb_motorista m ON m.matricula = '90002'
WHERE r.cod_map = 1002;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-09 05:30:00', '2026-07-09 13:30:00', '2026-07-09 06:20:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 503
JOIN tb_motorista m ON m.matricula = '90003'
WHERE r.cod_map = 1003;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-09 13:00:00', '2026-07-09 21:00:00', '2026-07-09 13:50:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 504
JOIN tb_motorista m ON m.matricula = '90004'
WHERE r.cod_map = 1004;

INSERT INTO tb_item_map (
    idmap, id_veiculo, id_motorista, hor_ini_jor, hor_fim_jor, chegada_ponto
)
SELECT r.id_registro, v.id_veiculo, m.id_motorista,
       '2026-07-09 22:00:00', '2026-07-10 06:00:00', '2026-07-09 22:40:00'
FROM tb_map r
JOIN tb_veiculo v ON v.codigo_veiculo = 501
JOIN tb_motorista m ON m.matricula = '90001'
WHERE r.cod_map = 1005;

-- Viagens vinculadas aos itens de registro (exemplos)
INSERT INTO tb_viagem (id_item_registro, horario_chegada, horario_saida, intervalo, qtd_pas_ida, qtd_pas_volta)
SELECT i.id_item, '2026-07-08 06:10:00', '2026-07-08 06:40:00', 30, 42, 38
FROM tb_item_map i
JOIN tb_map r ON r.id_registro = i.idmap
WHERE r.cod_map = 1001
ORDER BY i.id_item
LIMIT 1;

INSERT INTO tb_viagem (id_item_registro, horario_chegada, horario_saida, intervalo, qtd_pas_ida, qtd_pas_volta)
SELECT i.id_item, '2026-07-08 06:55:00', '2026-07-08 07:25:00', 30, 55, 50
FROM tb_item_map i
JOIN tb_map r ON r.id_registro = i.idmap
WHERE r.cod_map = 1001
ORDER BY i.id_item DESC
LIMIT 1;

INSERT INTO tb_viagem (id_item_registro, horario_chegada, horario_saida, intervalo, qtd_pas_ida, qtd_pas_volta)
SELECT i.id_item, '2026-07-08 14:15:00', '2026-07-08 14:50:00', 35, 60, NULL
FROM tb_item_map i
JOIN tb_map r ON r.id_registro = i.idmap
WHERE r.cod_map = 1002
ORDER BY i.id_item
LIMIT 1;
