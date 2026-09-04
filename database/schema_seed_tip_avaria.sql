-- Tipos de avaria — Tela Mensagem
USE map;

INSERT INTO tb_tip_avaria (id_tip, descricao) VALUES
    (1, 'PORTA QUEBRADA'),
    (2, 'VIDRO TRINCADO'),
    (3, 'PNEU FURADO'),
    (4, 'OUTROS')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);

ALTER TABLE tb_tip_avaria AUTO_INCREMENT = 5;
