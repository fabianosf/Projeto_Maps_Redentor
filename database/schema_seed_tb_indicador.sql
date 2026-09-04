-- Indicadores padrão (Tela 10 — RF-52) e vínculos exemplo Inspetor (RF-55)
USE map;

INSERT INTO tb_indicador (cod_ind, descricao, detalhe) VALUES
    (1, 'QTD(M)/ P', 'Quantidade média de passageiros'),
    (2, 'OCUP', 'Taxa de ocupação do veículo'),
    (3, 'ATR/M', 'Atraso médio no ponto'),
    (4, 'INT/V', 'Intervalo médio entre viagens'),
    (5, 'KMT/D', 'Quilometragem diária percorrida')
ON DUPLICATE KEY UPDATE
    descricao = VALUES(descricao),
    detalhe = VALUES(detalhe);

-- Inspetor (codigo_perfil = 3): QTD(M)/ P e OCUP habilitados (mockup doc)
INSERT INTO tb_ind_perf (id_ind, id_perfil)
SELECT i.id_ind, p.id_perfil
FROM tb_indicador i
CROSS JOIN tb_perfil p
WHERE p.codigo_perfil = 3
  AND i.cod_ind IN (1, 2)
ON DUPLICATE KEY UPDATE id_ind = id_ind;
