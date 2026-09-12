-- Seed local (PostgreSQL): motoristas fictícios para testar “Vincular motorista”.
-- Idempotente por matrícula temporária (uk_tb_motorista_matricula).
--
-- Identidade estável: id_motorista (PK). Vínculos em tb_item_map / guia usam id_motorista.
-- matricula é atributo sincronizável: pode ser atualizada no futuro com a matrícula
-- real da empresa SEM recriar o registro (UPDATE ... WHERE id_motorista = ?).
-- As matrículas TESTE00N são apenas temporárias de ambiente local — não dependência de produção.

INSERT INTO tb_motorista (matricula, nome, ativo) VALUES
    ('TESTE001', 'motorista_01', TRUE),
    ('TESTE002', 'motorista_02', TRUE),
    ('TESTE003', 'motorista_03', TRUE),
    ('TESTE004', 'motorista_04', TRUE),
    ('TESTE005', 'motorista_05', TRUE)
ON CONFLICT (matricula) DO UPDATE
SET
    nome = EXCLUDED.nome,
    ativo = TRUE;
