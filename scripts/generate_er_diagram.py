"""
Gera o diagrama Entidade-Relacionamento do banco 'map' como imagem PNG.
Usa apenas matplotlib (sem dependências externas de diagramas).
Saída: screenshots/er_diagram.png
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── Esquema do banco ──────────────────────────────────────────────────────────
TABLES = {
    'tb_perfil': [
        ('id_perfil',      'INT  PK'),
        ('codigo_perfil',  'INT  UNI'),
        ('descricao',      'VARCHAR(100)'),
    ],
    'tb_empresa': [
        ('id_empresa',      'INT  PK'),
        ('codigo_empresa',  'INT  UNI'),
        ('descricao',       'VARCHAR(100)'),
        ('ativo',           'TINYINT(1)'),
    ],
    'tb_local': [
        ('id_local',      'INT  PK'),
        ('codigo_local',  'INT  UNI'),
        ('descricao',     'VARCHAR(100)'),
        ('ativo',         'TINYINT(1)'),
    ],
    'tb_turno': [
        ('id_turno',      'INT  PK'),
        ('codigo_turno',  'INT  UNI'),
        ('descricao',     'VARCHAR(100)'),
        ('ativo',         'TINYINT(1)'),
    ],
    'tb_motorista': [
        ('id_motorista',  'INT  PK'),
        ('matricula',     'VARCHAR(20)  UNI'),
        ('nome',          'VARCHAR(150)'),
        ('ativo',         'TINYINT(1)'),
    ],
    'tb_veiculo': [
        ('id_veiculo',      'INT  PK'),
        ('codigo_veiculo',  'INT  UNI'),
        ('numero_frota',    'VARCHAR(20)  UNI'),
        ('placa',           'VARCHAR(10)  UNI'),
        ('ativo',           'TINYINT(1)'),
    ],
    'tb_usuario': [
        ('id_usuario',   'INT  PK'),
        ('matricula',    'VARCHAR(20)  UNI'),
        ('nome',         'VARCHAR(150)'),
        ('senha',        'VARCHAR(255)'),
        ('id_perfil',    'INT  FK'),
        ('ativo',        'TINYINT(1)'),
        ('trocar_senha', 'TINYINT(1)'),
    ],
    'tb_linha': [
        ('id_linha',           'INT  PK'),
        ('codigo_linha',       'INT  UNI'),
        ('id_empresa',         'INT  FK'),
        ('descricao',          'VARCHAR(150)'),
        ('id_local_origem',    'INT  FK'),
        ('id_local_destino',   'INT  FK'),
        ('ativo',              'TINYINT(1)'),
    ],
    'tb_map': [
        ('id_registro',        'INT  PK'),
        ('cod_map',            'INT  UNI'),
        ('id_usuario',         'INT  FK'),
        ('id_linha',           'INT  FK'),
        ('id_turno',           'INT  FK'),
        ('data',               'DATE'),
        ('inicio_jornada_des', 'DATETIME'),
        ('fim_jornada_des',    'DATETIME'),
        ('observacao',         'VARCHAR(500)'),
    ],
    'tb_item_map': [
        ('id_item',       'INT  PK'),
        ('idmap',         'INT  FK'),
        ('id_veiculo',    'INT  FK'),
        ('id_motorista',  'INT  FK'),
        ('hor_ini_jor',   'DATETIME'),
        ('hor_fim_jor',   'DATETIME'),
        ('chegada_ponto', 'DATETIME'),
    ],
    'tb_viagem': [
        ('id_viagem',       'INT  PK'),
        ('id_item_registro','INT  FK'),
        ('horario_chegada', 'DATETIME'),
        ('placa',           'VARCHAR(5)'),
        ('horario_saida',   'DATETIME'),
        ('intervalo',       'INT'),
        ('qtd_pas_ida',     'INT'),
        ('qtd_pas_volta',   'INT'),
    ],
}

# Relacionamentos: (tabela_filho, coluna_FK, tabela_pai, coluna_PK)
RELATIONS = [
    ('tb_usuario',  'id_perfil',         'tb_perfil',    'id_perfil'),
    ('tb_linha',    'id_empresa',         'tb_empresa',   'id_empresa'),
    ('tb_linha',    'id_local_origem',    'tb_local',     'id_local'),
    ('tb_linha',    'id_local_destino',   'tb_local',     'id_local'),
    ('tb_map',      'id_usuario',         'tb_usuario',   'id_usuario'),
    ('tb_map',      'id_linha',           'tb_linha',     'id_linha'),
    ('tb_map',      'id_turno',           'tb_turno',     'id_turno'),
    ('tb_item_map', 'idmap',              'tb_map',       'id_registro'),
    ('tb_item_map', 'id_veiculo',         'tb_veiculo',   'id_veiculo'),
    ('tb_item_map', 'id_motorista',       'tb_motorista', 'id_motorista'),
    ('tb_viagem',   'id_item_registro',   'tb_item_map',  'id_item'),
]

# ── Layout das tabelas (posição centro x, y  num grid 0..1) ──────────────────
# Dimensão do canvas: A4 landscape = ~29.7 × 21cm
# Usamos coordenadas normalizadas 0..1 nos dois eixos
POSITIONS = {
    #              cx,   cy
    'tb_perfil':      (0.08,  0.85),
    'tb_usuario':     (0.08,  0.50),
    'tb_empresa':     (0.35,  0.92),
    'tb_local':       (0.62,  0.92),
    'tb_turno':       (0.88,  0.92),
    'tb_motorista':   (0.88,  0.50),
    'tb_veiculo':     (0.88,  0.15),
    'tb_linha':       (0.48,  0.68),
    'tb_map':         (0.35,  0.42),
    'tb_item_map':    (0.55,  0.28),
    'tb_viagem':      (0.55,  0.06),
}

# ── Cores ─────────────────────────────────────────────────────────────────────
C_HEAD   = '#1a3a5c'   # azul escuro (cabeçalho)
C_HEAD_T = 'white'
C_PK     = '#e8f4fd'   # azul claro (PK)
C_FK     = '#fff7e6'   # amarelo claro (FK)
C_NORM   = '#f5f5f5'   # cinza claro (demais)
C_BORDER = '#1a3a5c'
C_REL    = '#c0392b'   # vermelho (setas)

FONT_HEAD  = dict(fontsize=7.5, fontweight='bold', color=C_HEAD_T,
                  ha='center', va='center', fontfamily='DejaVu Sans')
FONT_COL   = dict(fontsize=6.2, ha='left', va='center',
                  fontfamily='DejaVu Sans Mono')
FONT_TYPE  = dict(fontsize=5.8, color='#555555', ha='right', va='center',
                  fontfamily='DejaVu Sans Mono')

ROW_H   = 0.022   # altura de cada linha (coords norm.)
HEAD_H  = 0.030
PAD_X   = 0.007
TBL_W   = 0.165   # largura de cada tabela

# ── Figura ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 16.5, 11.5   # polegadas (A4 landscape ≈ 11.7×8.3)
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Desenhar tabelas e coletar posições das linhas para as setas ──────────────
# anchor_points[tabela][coluna] = (x_centro, y_centro_da_linha)
anchor_points = {}

for tname, cols in TABLES.items():
    if tname not in POSITIONS:
        continue
    cx, cy = POSITIONS[tname]
    n_rows = len(cols)
    total_h = HEAD_H + n_rows * ROW_H
    x0 = cx - TBL_W / 2
    y0 = cy - total_h / 2      # topo = cy + total_h/2, crescendo para baixo
    y_top = cy + total_h / 2

    anchor_points[tname] = {}

    # Cabeçalho
    head_rect = mpatches.FancyBboxPatch(
        (x0, y_top - HEAD_H), TBL_W, HEAD_H,
        boxstyle='square,pad=0',
        linewidth=1.0, edgecolor=C_BORDER, facecolor=C_HEAD, zorder=3,
    )
    ax.add_patch(head_rect)
    ax.text(cx, y_top - HEAD_H / 2, tname,
            zorder=4, **FONT_HEAD)

    # Linhas de colunas
    for i, (cname, ctype) in enumerate(cols):
        ry = y_top - HEAD_H - (i + 1) * ROW_H
        is_pk = 'PK' in ctype
        is_fk = 'FK' in ctype
        bg = C_PK if is_pk else (C_FK if is_fk else C_NORM)

        row_rect = mpatches.FancyBboxPatch(
            (x0, ry), TBL_W, ROW_H,
            boxstyle='square,pad=0',
            linewidth=0.5, edgecolor='#cccccc', facecolor=bg, zorder=3,
        )
        ax.add_patch(row_rect)

        label = cname
        if is_pk:
            label = '[PK] ' + cname
        elif is_fk:
            label = '[FK] ' + cname

        ax.text(x0 + PAD_X + 0.012, ry + ROW_H / 2, label,
                zorder=4, **FONT_COL)
        ax.text(x0 + TBL_W - PAD_X, ry + ROW_H / 2, ctype.split()[0],
                zorder=4, **FONT_TYPE)

        # ponto âncora = centro-direito da linha (para setas)
        anchor_points[tname][cname] = (cx + TBL_W / 2, ry + ROW_H / 2)

    # Borda externa da tabela
    brd = mpatches.FancyBboxPatch(
        (x0, y0), TBL_W, total_h,
        boxstyle='square,pad=0',
        linewidth=1.2, edgecolor=C_BORDER, facecolor='none', zorder=5,
    )
    ax.add_patch(brd)

# ── Desenhar relacionamentos ──────────────────────────────────────────────────
def anchor(tname, col):
    """Retorna (x_esq, y) e (x_dir, y) para um campo."""
    if tname not in anchor_points or col not in anchor_points.get(tname, {}):
        cx, cy = POSITIONS[tname]
        return (cx - TBL_W/2, cy), (cx + TBL_W/2, cy)
    x, y = anchor_points[tname][col]
    return (x - TBL_W, y), (x, y)

drawn = set()
for (t_from, col_from, t_to, col_to) in RELATIONS:
    key = (t_from, col_from, t_to, col_to)
    if key in drawn:
        continue
    drawn.add(key)

    _, (xf, yf) = anchor(t_from, col_from)
    (xt, yt), _ = anchor(t_to, col_to)

    # Decidir de que lado sair/entrar dependendo da posição relativa
    cx_f = POSITIONS[t_from][0]
    cx_t = POSITIONS[t_to][0]
    if cx_f <= cx_t:
        xf_end = POSITIONS[t_from][0] + TBL_W / 2
        xt_end = POSITIONS[t_to][0]   - TBL_W / 2
    else:
        xf_end = POSITIONS[t_from][0] - TBL_W / 2
        xt_end = POSITIONS[t_to][0]   + TBL_W / 2

    ax.annotate(
        '', xy=(xt_end, yt), xytext=(xf_end, yf),
        arrowprops=dict(
            arrowstyle='-|>',
            color=C_REL,
            lw=1.0,
            connectionstyle='arc3,rad=0.0',
        ),
        zorder=2,
    )

# ── Título ────────────────────────────────────────────────────────────────────
ax.text(0.5, 0.995, 'Diagrama',
        ha='center', va='top', fontsize=14, fontweight='bold',
        color=C_HEAD, fontfamily='DejaVu Sans',
        transform=ax.transAxes)

# ── Legenda ───────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=C_PK,   edgecolor='#aaa', label='Chave Primária (PK)'),
    mpatches.Patch(facecolor=C_FK,   edgecolor='#aaa', label='Chave Estrangeira (FK)'),
    mpatches.Patch(facecolor=C_NORM, edgecolor='#aaa', label='Atributo'),
    mpatches.Patch(facecolor=C_REL,  edgecolor=C_REL,  label='Relacionamento'),
]
ax.legend(handles=legend_items, loc='lower right',
          fontsize=7, framealpha=0.9, edgecolor='#cccccc',
          bbox_to_anchor=(1.0, 0.0))

plt.tight_layout(pad=0.3)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'screenshots', 'er_diagram.png')
plt.savefig(OUT, dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Diagrama salvo: {OUT}')
