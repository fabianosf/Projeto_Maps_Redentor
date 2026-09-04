-- Migração: vínculos de Despachante em tb_usuario (empresa, turno, local)
USE map;

ALTER TABLE tb_usuario
  ADD COLUMN id_empresa INT NULL COMMENT 'FK tb_empresa — Despachante' AFTER id_perfil,
  ADD COLUMN id_turno   INT NULL COMMENT 'FK tb_turno — Despachante' AFTER id_empresa,
  ADD COLUMN id_local   INT NULL COMMENT 'FK tb_local — Despachante' AFTER id_turno;

ALTER TABLE tb_usuario
  ADD KEY idx_tb_usuario_id_empresa (id_empresa),
  ADD KEY idx_tb_usuario_id_turno (id_turno),
  ADD KEY idx_tb_usuario_id_local (id_local),
  ADD CONSTRAINT fk_tb_usuario_empresa
      FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa),
  ADD CONSTRAINT fk_tb_usuario_turno
      FOREIGN KEY (id_turno) REFERENCES tb_turno (id_turno),
  ADD CONSTRAINT fk_tb_usuario_local
      FOREIGN KEY (id_local) REFERENCES tb_local (id_local);
