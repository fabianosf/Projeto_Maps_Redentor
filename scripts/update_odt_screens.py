"""
Gera mockups de celular Samsung A03 para cada tela e
substitui o capítulo 8 do documento ODT com as novas imagens.

Uso:
    python scripts/update_odt_screens.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

from PIL import Image, ImageDraw

# ─── Caminhos ─────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS    = os.path.join(BASE_DIR, 'screenshots')
MOCKUPS        = os.path.join(SCREENSHOTS, 'mockups')
ODT_ORIG       = os.path.join(BASE_DIR, 'Doc', 'Doc_Proj_Map.odt')
ODT_BACKUP     = ODT_ORIG.replace('.odt', '_backup.odt')
ODT_OUT        = ODT_ORIG  # sobrescreve o original

os.makedirs(MOCKUPS, exist_ok=True)

# ─── Telas (ordem de apresentação) ────────────────────────────────────────────
TELAS = [
    ('01_login.png',              'Tela 01 - Login'),
    ('02_cadastro_senha.png',     'Tela 02 - Cadastro de Senha'),
    ('11_usuarios.png',           'Tela 03 - Cadastro de Usuario'),
    ('10_principal.png',          'Tela 04 - Principal (RedMapa)'),
    ('03_lista_mapa.png',         'Tela 05 - Lista de Mapas'),
    ('04_cadastro_mapa.png',      'Tela 06 - Cadastro de Mapa'),
    ('05_registros.png',          'Tela 07 - Registros do Mapa'),
    ('06_cadastro_registro.png',  'Tela 08 - Cadastro de Registro'),
    ('07_viagens.png',            'Tela 09 - Viagens'),
    ('08_cadastro_viagem.png',    'Tela 10 - Cadastro de Viagem'),
    ('13_configuracao.png',       'Tela 11 - Configuracao'),
]

# ─── Parâmetros do mockup Samsung A03 ─────────────────────────────────────────
# A03: 720×1600 display; nosso viewport capturado: 360×800 CSS px
BEZEL_SIDE   = 28   # px
BEZEL_TOP    = 90   # inclui área da câmera
BEZEL_BOTTOM = 70
CORNER_R     = 36   # raio das bordas arredondadas
BODY_COLOR   = (24, 24, 28)
BEZEL_COLOR  = (50, 50, 55)
CAM_COLOR    = (8, 8, 10)


def make_mockup(screen_path: str, out_path: str) -> tuple[int, int]:
    """Cria mockup de celular com fundo transparente (sem área branca externa)."""
    screen = Image.open(screen_path).convert('RGBA')
    sw, sh = screen.size

    fw = sw + 2 * BEZEL_SIDE
    fh = sh + BEZEL_TOP + BEZEL_BOTTOM

    # Fundo completamente transparente
    phone = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(phone)

    # Corpo do telefone (rounded rectangle com alpha sólido)
    draw.rounded_rectangle(
        [(0, 0), (fw - 1, fh - 1)],
        radius=CORNER_R,
        fill=BODY_COLOR + (255,),
        outline=BEZEL_COLOR + (255,),
        width=3,
    )

    # Área da tela (branca opaca)
    sx, sy = BEZEL_SIDE, BEZEL_TOP
    draw.rectangle([(sx, sy), (sx + sw - 1, sy + sh - 1)], fill=(255, 255, 255, 255))

    # Câmera (hole-punch) centralizada no topo
    cx, cy = fw // 2, BEZEL_TOP // 2 + 4
    draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=CAM_COLOR + (255,))
    draw.ellipse([(cx - 7,  cy - 7),  (cx + 7,  cy + 7)],  fill=(15, 15, 20, 255))

    # Barra de navegação (indicador home)
    bw = 70
    bx = (fw - bw) // 2
    by = fh - BEZEL_BOTTOM + 22
    draw.rounded_rectangle(
        [(bx, by), (bx + bw, by + 5)],
        radius=3,
        fill=(120, 120, 130, 255),
    )

    # Colar screenshot dentro da área da tela
    phone.paste(screen, (sx, sy), screen)

    # Salvar como PNG com transparência (sem converter para RGB)
    phone.save(out_path, 'PNG', optimize=True)

    return fw, fh


# ─── 1. Gerar mockups ─────────────────────────────────────────────────────────
print('Gerando mockups...')
mockup_info = []  # lista de (filename_in_zip, w_px, h_px, titulo)
for fname, titulo in TELAS:
    src = os.path.join(SCREENSHOTS, fname)
    if not os.path.exists(src):
        print(f'  [SKIP] {fname} não encontrado')
        continue
    dst = os.path.join(MOCKUPS, fname)
    w, h = make_mockup(src, dst)
    pic_name = f'Pictures/screen_{fname}'
    mockup_info.append((fname, w, h, titulo, pic_name))
    print(f'  OK {titulo}: {w}x{h} px')

# ─── 2. Fazer backup e ler ODT ────────────────────────────────────────────────
print()
print('Atualizando documento ODT...')
shutil.copy2(ODT_ORIG, ODT_BACKUP)
print(f'  Backup: {ODT_BACKUP}')

with zipfile.ZipFile(ODT_ORIG, 'r') as z_in:
    odt_files = {}
    for name in z_in.namelist():
        odt_files[name] = z_in.read(name)

content = odt_files['content.xml'].decode('utf-8')

# ─── 3. Localizar região do capítulo 8 no XML ─────────────────────────────────
# O capítulo começa com um text:p que contém "8.) Interface gráfica"
# e termina antes do próximo capítulo de mesmo nível (ou fim do body).

# Procurar início: o text:p que abre um page-break antes do capítulo 8
IDX_CAP8_START_MARKER = 'Interface gráfica ( Front End)'
IDX_CAP8_START = content.rfind('<text:p', 0, content.find(IDX_CAP8_START_MARKER))

# Procurar fim: próximo capítulo de nível 9 ou seção equivalente
# Como não há capítulo 9 visível, buscamos o final do body
end_markers = ['</office:text>', '</office:body>']
IDX_CAP8_END = len(content)
for marker in end_markers:
    idx = content.find(marker)
    if idx > IDX_CAP8_START and idx < IDX_CAP8_END:
        IDX_CAP8_END = idx

print(f'  Região do cap 8: {IDX_CAP8_START}..{IDX_CAP8_END} ({IDX_CAP8_END - IDX_CAP8_START} chars)')

# ─── 4. Montar novo conteúdo XML para o capítulo 8 ────────────────────────────
# Dimensões A4 com margens de 2.5cm: largura útil ≈ 16cm
# Imagem ocupa ~1/3 da página em largura → 5.5cm de largura
# Altura proporcional ao mockup
IMG_WIDTH_CM  = 5.486  # 5.225 * 1.05
IMG_X_CM      = 5.257  # (16 - 5.486) / 2

style_heading = 'P125'   # estilo do capítulo 8

def cm(val: float) -> str:
    return f'{val:.3f}cm'


def img_xml(pic_name: str, w_px: int, h_px: int,
            frame_name: str, z_idx: int) -> str:
    """Gera XML do draw:frame com a imagem, centralizado na página."""
    aspect = h_px / w_px
    img_w = IMG_WIDTH_CM
    img_h = round(img_w * aspect, 3)
    x     = IMG_X_CM

    return (
        f'<draw:frame draw:style-name="fr3" draw:name="{frame_name}" '
        f'text:anchor-type="paragraph" '
        f'svg:x="{cm(x)}" svg:width="{cm(img_w)}" svg:height="{cm(img_h)}" '
        f'draw:z-index="{z_idx}">'
        f'<draw:image xlink:href="{pic_name}" '
        f'xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad" '
        f'draw:mime-type="image/png"/>'
        f'</draw:frame>'
    )


new_parts = []

# Linha de abertura do capítulo (mantém heading original)
new_parts.append(
    f'<text:p text:style-name="{style_heading}">'
    f'<text:span text:style-name="T93">8</text:span>'
    f'.) Interface gr\u00e1fica ( Front End)</text:p>'
)
new_parts.append(f'<text:p text:style-name="{style_heading}"/>')

for i, (fname, w, h, titulo, pic_name) in enumerate(mockup_info):
    # Quebra de página antes de cada tela (exceto a primeira que já tem)
    if i > 0:
        new_parts.append(
            f'<text:p text:style-name="{style_heading}">'
            f'<text:soft-page-break/></text:p>'
        )
    # Título da tela
    new_parts.append(
        f'<text:p text:style-name="{style_heading}">'
        f'<text:span text:style-name="T93">{titulo}</text:span></text:p>'
    )
    new_parts.append(f'<text:p text:style-name="{style_heading}"/>')
    # Parágrafo com imagem
    new_parts.append(
        f'<text:p text:style-name="{style_heading}">'
        + img_xml(pic_name, w, h, f'ScreenFig{i+1:02d}', 100 + i)
        + f'</text:p>'
    )
    new_parts.append(f'<text:p text:style-name="{style_heading}"/>')

new_chapter_xml = ''.join(new_parts)

# ─── 5. Substituir no content.xml ─────────────────────────────────────────────
new_content = content[:IDX_CAP8_START] + new_chapter_xml + content[IDX_CAP8_END:]
odt_files['content.xml'] = new_content.encode('utf-8')

# ─── 6. Adicionar imagens ao manifest e ao ZIP ────────────────────────────────
manifest = odt_files['META-INF/manifest.xml'].decode('utf-8')

new_manifest_entries = []
for fname, w, h, titulo, pic_name in mockup_info:
    mockup_path = os.path.join(MOCKUPS, fname)
    with open(mockup_path, 'rb') as f:
        odt_files[pic_name] = f.read()

    entry = (
        f'<manifest:file-entry manifest:full-path="{pic_name}" '
        f'manifest:media-type="image/png"/>'
    )
    if pic_name not in manifest:
        new_manifest_entries.append(entry)

if new_manifest_entries:
    insert_before = '</manifest:manifest>'
    manifest = manifest.replace(
        insert_before,
        '\n'.join(new_manifest_entries) + '\n' + insert_before,
    )
    odt_files['META-INF/manifest.xml'] = manifest.encode('utf-8')

# ─── 7. Escrever novo ODT ─────────────────────────────────────────────────────
tmp_path = ODT_OUT + '.tmp'
with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as z_out:
    # 'mimetype' deve ser o primeiro arquivo e sem compressão
    z_out.writestr(
        zipfile.ZipInfo('mimetype'),
        odt_files.get('mimetype', b'application/vnd.oasis.opendocument.text'),
        compress_type=zipfile.ZIP_STORED,
    )
    for name, data in odt_files.items():
        if name == 'mimetype':
            continue
        z_out.writestr(name, data)

os.replace(tmp_path, ODT_OUT)
print(f'  ODT atualizado: {ODT_OUT}')
print()
print('Concluído!')
print(f'  Telas inseridas: {len(mockup_info)}')
print(f'  Backup original: {ODT_BACKUP}')
