-- Corrige descrições invertidas em tb_perfil (doc: 2=Despachante, 3=Inspetor)
USE map;

UPDATE tb_perfil SET descricao = 'Despachante' WHERE codigo_perfil = 2;
UPDATE tb_perfil SET descricao = 'Inspetor' WHERE codigo_perfil = 3;
