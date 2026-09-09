-- DesignacaoOperacional: histórico de alocação do despachante (não sobrescreve).
-- MariaDB: "uma ATIVA por usuário" garantida na aplicação/transação (sem índice parcial).

USE map;

CREATE TABLE IF NOT EXISTS tb_designacao_operacional (
    id_designacao   INT          NOT NULL AUTO_INCREMENT,
    id_usuario      INT          NOT NULL COMMENT 'FK tb_usuario — despachante',
    id_empresa      INT          NOT NULL COMMENT 'FK tb_empresa',
    id_turno        INT          NOT NULL COMMENT 'FK tb_turno',
    id_linha        INT          NULL     COMMENT 'FK tb_linha — opcional',
    id_veiculo      INT          NULL     COMMENT 'FK tb_veiculo — opcional',
    data            DATE         NOT NULL COMMENT 'Data da designação',
    inicio          DATETIME     NOT NULL COMMENT 'Início da vigência',
    fim             DATETIME     NULL     COMMENT 'Fim da vigência — NULL se ATIVA',
    status          VARCHAR(20)  NOT NULL DEFAULT 'ATIVA' COMMENT 'ATIVA | ENCERRADA',
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    encerrado_em    DATETIME     NULL,
    id_admin        INT          NULL     COMMENT 'FK tb_usuario — quem criou/transferiu',
    PRIMARY KEY (id_designacao),
    KEY idx_desig_id_usuario (id_usuario),
    KEY idx_desig_usuario_status (id_usuario, status),
    KEY idx_desig_empresa (id_empresa),
    KEY idx_desig_turno (id_turno),
    KEY idx_desig_linha (id_linha),
    KEY idx_desig_veiculo (id_veiculo),
    CONSTRAINT fk_desig_usuario
        FOREIGN KEY (id_usuario) REFERENCES tb_usuario (id_usuario),
    CONSTRAINT fk_desig_empresa
        FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
    CONSTRAINT fk_desig_turno
        FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
    CONSTRAINT fk_desig_linha
        FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha),
    CONSTRAINT fk_desig_veiculo
        FOREIGN KEY (id_veiculo) REFERENCES tb_veiculo (id_veiculo),
    CONSTRAINT fk_desig_admin
        FOREIGN KEY (id_admin) REFERENCES tb_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed legado: ATIVA com empresa/turno do usuário; linha/veículo NULL (não inventar).
INSERT INTO tb_designacao_operacional (
    id_usuario, id_empresa, id_turno, id_linha, id_veiculo,
    data, inicio, fim, status, criado_em, encerrado_em, id_admin
)
SELECT
    u.id_usuario,
    u.id_empresa,
    u.id_turno,
    NULL,
    NULL,
    CURDATE(),
    NOW(),
    NULL,
    'ATIVA',
    NOW(),
    NULL,
    NULL
FROM tb_usuario u
INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
WHERE p.codigo_perfil = 2
  AND u.ativo = 1
  AND u.id_empresa IS NOT NULL
  AND u.id_turno IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM tb_designacao_operacional d
      WHERE d.id_usuario = u.id_usuario
        AND d.status = 'ATIVA'
  );
