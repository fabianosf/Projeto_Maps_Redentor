-- Dados base Proj_Map — FKs por PK, IDs explícitos a partir de 0
USE map;

SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');

INSERT INTO tb_perfil (id_perfil, codigo_perfil, descricao) VALUES
    (0, 1, 'Administrador'),
    (1, 2, 'Despachante'),
    (2, 3, 'Inspetor');

INSERT INTO tb_empresa (id_empresa, codigo_empresa, descricao, ativo) VALUES
    (0, 1, 'Redentor', 1),
    (1, 2, 'Futuro', 1),
    (2, 3, 'Barra', 1);

INSERT INTO tb_turno (id_turno, codigo_turno, descricao, ativo) VALUES
    (0, 1, 'TURNO 01', 1),
    (1, 2, 'TURNO 02', 1),
    (2, 3, 'TURNO 03', 1);

INSERT INTO tb_local (id_local, codigo_local, descricao, ativo) VALUES
    (0, 37, 'Cidade De Deus', 1),
    (1, 31, 'Gavea', 1),
    (2, 42, 'Tanque', 1),
    (3, 25, 'Taquara', 1),
    (4, 84, 'Copacabana', 1),
    (5, 34, 'Jardim Oceanico', 1),
    (6, 62, 'Downtown', 1),
    (7, 69, 'Candelaria', 1);

INSERT INTO tb_linha (
    id_linha, codigo_linha, id_empresa, descricao,
    id_local_origem, id_local_destino, ativo
) VALUES
    (
        0, 1, 2, 'Cidade De Deus - Gavea',
        (SELECT id_local FROM tb_local WHERE codigo_local = 37),
        (SELECT id_local FROM tb_local WHERE codigo_local = 31),
        0
    ),
    (
        1, 2, 1, 'Tanque - Gavea',
        (SELECT id_local FROM tb_local WHERE codigo_local = 42),
        (SELECT id_local FROM tb_local WHERE codigo_local = 31),
        0
    ),
    (
        2, 3, 2, 'Rio Das Pedras - Copacabana',
        (SELECT id_local FROM tb_local WHERE codigo_local = 25),
        (SELECT id_local FROM tb_local WHERE codigo_local = 84),
        0
    ),
    (
        3, 4, 2, 'Taquara - DownTown',
        (SELECT id_local FROM tb_local WHERE codigo_local = 25),
        (SELECT id_local FROM tb_local WHERE codigo_local = 62),
        0
    ),
    (
        4, 5, 1, 'Jardim Oceanico - Candelaria',
        (SELECT id_local FROM tb_local WHERE codigo_local = 34),
        (SELECT id_local FROM tb_local WHERE codigo_local = 69),
        0
    );

ALTER TABLE tb_perfil AUTO_INCREMENT = 3;
ALTER TABLE tb_empresa AUTO_INCREMENT = 3;
ALTER TABLE tb_turno AUTO_INCREMENT = 3;
ALTER TABLE tb_local AUTO_INCREMENT = 8;
ALTER TABLE tb_linha AUTO_INCREMENT = 5;

INSERT INTO tb_usuario (
    matricula, nome, senha, id_perfil,
    id_empresa, id_turno, id_local, ativo, trocar_senha
)
SELECT
    '59492',
    'Administrador',
    '$2b$12$iL5/TnNloKB9HEpqZ/lP9u2IU9rsp0q.jaaE7NmlztVtQ3sCOHaWO',
    p.id_perfil,
    NULL, NULL, NULL, 1, 0
FROM tb_perfil p
WHERE p.codigo_perfil = 1
LIMIT 1;
