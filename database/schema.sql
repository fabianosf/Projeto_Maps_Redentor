-- Setup completo do banco MAP (executar como root)
-- Critérios: nomenclatura clara, tipos adequados, FKs pela PK, normalização 3FN
--
-- Conexão MariaDB local:
--   Host: localhost   Porta: 3306   Usuário: root   Senha: senha   Banco: map
--
-- Política de senha (tb_usuario.senha) — Doc_Proj_Map.odt (RF-RN-004, RF-RN-006):
--   • Nunca texto puro; sempre hash bcrypt (cost 12), formato $2b$12$...
--   • Cadastro inicial / reset Admin: hash de "12345"; trocar_senha = 1 (DEFAULT)
--   • RedMapa — login: valida senha digitada contra hash (bcrypt.verify; não descriptografa)
--   • RedMapa — 1º acesso: grava novo hash bcrypt da senha definitiva; trocar_senha = 0
--   • Seeds dev (1001/1002): hash de "12345", trocar_senha = 0 (pula fluxo de 1º acesso)
--
-- Hash bcrypt de referência para senha "12345":
--   $2b$12$EwK./Ga3s71.6obLv.Pm0u1j5C1mrfKAAv.ai2rtNkbPXarqB7Wqm

CREATE DATABASE IF NOT EXISTS map
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'usumap'@'localhost' IDENTIFIED BY 'senha';
GRANT ALL PRIVILEGES ON map.* TO 'usumap'@'localhost';
FLUSH PRIVILEGES;

USE map;

CREATE TABLE IF NOT EXISTS tb_perfil (
    id_perfil       INT          NOT NULL AUTO_INCREMENT,
    codigo_perfil   INT          NOT NULL COMMENT 'Código de negócio do perfil',
    descricao       VARCHAR(100) NOT NULL COMMENT 'Descrição do perfil',
    PRIMARY KEY (id_perfil),
    UNIQUE KEY uk_tb_perfil_codigo (codigo_perfil)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tb_usuario (
    id_usuario      INT          NOT NULL AUTO_INCREMENT,
    matricula       VARCHAR(20)  NOT NULL COMMENT 'Matrícula de login',
    nome            VARCHAR(150) NOT NULL,
    senha           VARCHAR(255) NOT NULL COMMENT 'Hash bcrypt (provisória ou definitiva)',
    id_perfil       INT          NOT NULL COMMENT 'FK tb_perfil.id_perfil',
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    trocar_senha    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '1 = primeiro acesso / troca obrigatória',
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uk_tb_usuario_matricula (matricula),
    KEY idx_tb_usuario_id_perfil (id_perfil),
    KEY idx_tb_usuario_trocar_senha (trocar_senha),
    CONSTRAINT fk_tb_usuario_perfil
        FOREIGN KEY (id_perfil) REFERENCES tb_perfil (id_perfil)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO tb_perfil (codigo_perfil, descricao) VALUES
    (1, 'Administrador'),
    (2, 'Despachante')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);

-- Seeds de desenvolvimento: senha em texto claro = 12345 (hash bcrypt abaixo)
INSERT INTO tb_usuario (matricula, nome, senha, id_perfil, trocar_senha)
SELECT
    '1001',
    'Usuário Administrador',
    '$2b$12$EwK./Ga3s71.6obLv.Pm0u1j5C1mrfKAAv.ai2rtNkbPXarqB7Wqm',
    p.id_perfil,
    0
FROM tb_perfil p
WHERE p.codigo_perfil = 1
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome),
    senha = VALUES(senha),
    id_perfil = VALUES(id_perfil),
    trocar_senha = VALUES(trocar_senha);

INSERT INTO tb_usuario (matricula, nome, senha, id_perfil, trocar_senha)
SELECT
    '1002',
    'Usuário Despachante',
    '$2b$12$EwK./Ga3s71.6obLv.Pm0u1j5C1mrfKAAv.ai2rtNkbPXarqB7Wqm',
    p.id_perfil,
    0
FROM tb_perfil p
WHERE p.codigo_perfil = 2
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome),
    senha = VALUES(senha),
    id_perfil = VALUES(id_perfil),
    trocar_senha = VALUES(trocar_senha);
