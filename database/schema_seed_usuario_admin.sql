-- Usuários administradores Proj_Map (senha: Admin_2026 — hash gerado em scripts/aplicar_admins_proj_map.py)
USE map;

-- Remover registros anteriores destas matrículas (se existirem)
DELETE FROM tb_avaria
WHERE id_usuario IN (
    SELECT id_usuario FROM tb_usuario WHERE matricula IN ('59492', '59817')
);

DELETE FROM tb_usuario WHERE matricula IN ('59492', '59817');

INSERT INTO tb_usuario (
    matricula,
    nome,
    senha,
    id_perfil,
    id_empresa,
    id_turno,
    id_local,
    ativo,
    trocar_senha
)
SELECT
    v.matricula,
    v.nome,
    '$2b$12$PLACEHOLDER_RUN_aplicar_admins_proj_map_py',
    p.id_perfil,
    NULL,
    NULL,
    NULL,
    1,
    0
FROM (
    SELECT '59492' AS matricula, 'Marcos Antônio Correa Jordão' AS nome
    UNION ALL
    SELECT '59817', 'Fabiano Souza De Freitas'
) AS v
CROSS JOIN tb_perfil p
WHERE p.codigo_perfil = 1;
