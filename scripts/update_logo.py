"""
Edita logo-mapa-3d.png: substitui o texto 'Mapa' por 'RedMapa'
usando como base o logo-mapa-3d-original.png (backup limpo).
"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw, ImageFont
import numpy as np

ASSETS = r"E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP\FrontEnd\src\assets"
SRC    = os.path.join(ASSETS, "logo-mapa-3d-original.png")
DST    = os.path.join(ASSETS, "logo-mapa-3d.png")

if not os.path.exists(SRC):
    # Se o original não existir, usa o arquivo atual como base e faz backup
    shutil.copy2(DST, SRC)
    print("Backup criado: logo-mapa-3d-original.png")

img = Image.open(SRC).convert("RGBA")
W, H = img.size
print(f"Imagem: {W}x{H}")

arr = np.array(img, dtype=np.float32)

# ── 1. Cobrir a área do texto "Mapa" de forma suave ───────────────────────────
# O texto "Mapa" fica ABAIXO do ônibus, na parte inferior interna do círculo.
# Parâmetros ajustados para 1024x976:
cover_y1 = int(H * 0.72)   # início do texto (abaixo do ônibus)
cover_y2 = int(H * 0.845)  # fim do texto (acima da borda azul do círculo)

# Linha de referência: uma faixa limpa acima do "Mapa" (interior branco do círculo)
ref_y1 = int(H * 0.695)
ref_y2 = int(H * 0.715)

# Calcular a média das linhas de referência para obter cor de fundo uniforme
ref_rows = arr[ref_y1:ref_y2].astype(np.float32)
ref_avg  = ref_rows.mean(axis=0)  # shape (W, 4)

# Preenchimento: cobre todos os pixels na faixa horizontal do texto
# (excluindo apenas os extremos laterais onde fica a borda azul do círculo)
x_margin_left  = int(W * 0.16)   # começo dentro do círculo
x_margin_right = int(W * 0.84)   # fim dentro do círculo

for y in range(cover_y1, cover_y2):
    row_alpha = arr[y, :, 3]
    inside_circle = row_alpha > 20
    # Limitar ao interior horizontal (excluir borda)
    x_mask = np.zeros(W, dtype=bool)
    x_mask[x_margin_left:x_margin_right] = True
    to_fill = inside_circle & x_mask
    arr[y][to_fill] = ref_avg[to_fill]

img = Image.fromarray(arr.astype(np.uint8))
draw = ImageDraw.Draw(img)

# ── 2. Desenhar "RedMapa" no mesmo estilo ─────────────────────────────────────
TEXT  = "RedMapa"
COLOR_MAIN   = (20, 40, 100, 255)   # azul escuro ~#142864
COLOR_SHADOW = (10, 20,  60, 180)   # sombra mais escura

# Tentar fontes bold disponíveis no Windows
font_candidates = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
]
font_path = next((f for f in font_candidates if os.path.exists(f)), None)

# Tamanho da fonte proporcional à imagem
font_size = int(H * 0.115)   # ~118px para imagem 1024
if font_path:
    font = ImageFont.truetype(font_path, font_size)
    print(f"Fonte: {font_path}  tamanho: {font_size}")
else:
    font = ImageFont.load_default()
    print("Usando fonte padrão")

# Centro horizontal e vertical do texto
cx = W // 2
cy = int(H * 0.785)

bbox = draw.textbbox((0, 0), TEXT, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
tx = cx - tw // 2
ty = cy - th // 2

# Sombra/profundidade (offset 3px)
for ox, oy in [(3, 3), (2, 2), (1, 1)]:
    draw.text((tx + ox, ty + oy), TEXT, font=font, fill=COLOR_SHADOW)

# Texto principal
draw.text((tx, ty), TEXT, font=font, fill=COLOR_MAIN)

# ── 3. Salvar ─────────────────────────────────────────────────────────────────
img.save(DST, "PNG", optimize=True)
print(f"Salvo: {DST}")
