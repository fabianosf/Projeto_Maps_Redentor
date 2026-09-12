-- PostgreSQL: plantão do MAPA como TIME (data fica em tb_map.data).
-- Idempotente. Preserva a parte horária de valores TIMESTAMP existentes.

ALTER TABLE tb_map
    ALTER COLUMN inicio_jornada_des TYPE TIME
    USING (
        CASE
            WHEN inicio_jornada_des IS NULL THEN TIME '00:00'
            ELSE inicio_jornada_des::time
        END
    );

ALTER TABLE tb_map
    ALTER COLUMN fim_jornada_des TYPE TIME
    USING (
        CASE
            WHEN fim_jornada_des IS NULL THEN NULL
            ELSE fim_jornada_des::time
        END
    );

-- Ambos obrigatórios no cadastro atual; preenche nulos legados (mín. +1 min).
UPDATE tb_map
SET fim_jornada_des = (inicio_jornada_des + INTERVAL '1 minute')
WHERE fim_jornada_des IS NULL;

ALTER TABLE tb_map
    ALTER COLUMN fim_jornada_des SET NOT NULL;
