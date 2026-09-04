-- Reseed Proj_Map — recarrega cadastros base (truncate via script Python)
USE map;

SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');
INSERT INTO tb_perfil (id_perfil, codigo_perfil, descricao) VALUES
    (0, 1, 'Administrador'),
    (1, 2, 'Despachante'),
    (2, 3, 'Inspetor');

-- 2) Empresas
INSERT INTO tb_empresa (id_empresa, codigo_empresa, descricao, ativo) VALUES
    (0, 1, 'Redentor', 1),
    (1, 2, 'Futuro', 1),
    (2, 3, 'Barra', 1);

-- 3) Turnos
INSERT INTO tb_turno (id_turno, codigo_turno, descricao, ativo) VALUES
    (0, 1, 'TURNO 01', 1),
    (1, 2, 'TURNO 02', 1),
    (2, 3, 'TURNO 03', 1);

-- 5) Locais
INSERT INTO tb_local (id_local, codigo_local, descricao, ativo) VALUES
    (0, 37, 'Cidade De Deus', 1),
    (1, 31, 'Gavea', 1),
    (2, 42, 'Tanque', 1),
    (3, 25, 'Taquara', 1),
    (4, 84, 'Copacabana', 1),
    (5, 34, 'Jardim Oceanico', 1),
    (6, 62, 'Downtown', 1),
    (7, 69, 'Candelaria', 1);

-- 6) Linhas (origem/destino por codigo_local → id_local)
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
    v.matricula,
    v.nome,
    '$2b$12$PLACEHOLDER_RUN_aplicar_admins_proj_map_py',
    p.id_perfil,
    NULL, NULL, NULL, 1, 0
FROM (
    SELECT '59492' AS matricula, 'Marcos Antônio Correa Jordão' AS nome
    UNION ALL
    SELECT '59817', 'Fabiano Souza De Freitas'
) AS v
CROSS JOIN tb_perfil p
WHERE p.codigo_perfil = 1;
