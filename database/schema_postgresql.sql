-- Banco MAP — PostgreSQL (autenticação)
CREATE DATABASE map
  WITH ENCODING 'UTF8'
  LC_COLLATE 'Portuguese_Brazil.1252'
  LC_CTYPE 'Portuguese_Brazil.1252'
  TEMPLATE template0;

\c map

CREATE TABLE IF NOT EXISTS tb_perfil (
    id_perfil       SERIAL       PRIMARY KEY,
    codigo_perfil   INT          NOT NULL UNIQUE,
    descricao       VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_usuario (
    id_usuario      SERIAL       PRIMARY KEY,
    matricula       VARCHAR(20)  NOT NULL UNIQUE,
    nome            VARCHAR(150) NOT NULL,
    senha           VARCHAR(255) NOT NULL,
    id_perfil       INT          NOT NULL REFERENCES tb_perfil (id_perfil),
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    trocar_senha    BOOLEAN      NOT NULL DEFAULT TRUE
);

INSERT INTO tb_perfil (codigo_perfil, descricao) VALUES
    (1, 'Administrador'),
    (2, 'Despachante')
ON CONFLICT (codigo_perfil) DO UPDATE SET descricao = EXCLUDED.descricao;

INSERT INTO tb_usuario (matricula, nome, senha, id_perfil, trocar_senha)
SELECT
    '1001',
    'Usuário Administrador',
    '$2b$12$5BFsUGnID56bNi.GVgqPh.EZhzIY4Q35qFds98usd2Hi7.8O8OOIO',
    p.id_perfil,
    FALSE
FROM tb_perfil p
WHERE p.codigo_perfil = 1
ON CONFLICT (matricula) DO UPDATE SET
    nome = EXCLUDED.nome,
    senha = EXCLUDED.senha,
    id_perfil = EXCLUDED.id_perfil,
    trocar_senha = EXCLUDED.trocar_senha;

INSERT INTO tb_usuario (matricula, nome, senha, id_perfil, trocar_senha)
SELECT
    '1002',
    'Usuário Despachante',
    '$2b$12$5BFsUGnID56bNi.GVgqPh.EZhzIY4Q35qFds98usd2Hi7.8O8OOIO',
    p.id_perfil,
    FALSE
FROM tb_perfil p
WHERE p.codigo_perfil = 2
ON CONFLICT (matricula) DO UPDATE SET
    nome = EXCLUDED.nome,
    senha = EXCLUDED.senha,
    id_perfil = EXCLUDED.id_perfil,
    trocar_senha = EXCLUDED.trocar_senha;
