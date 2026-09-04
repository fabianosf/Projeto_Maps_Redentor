"""
Adiciona o capítulo 'Banco De Dados' com diagrama ER em página PAISAGEM.
Deve ser executado APÓS rebuild_odt_ch8.py.
"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAGRAM_IMG = os.path.join(BASE_DIR, 'screenshots', 'er_diagram.png')
ODT_PATH    = os.path.join(BASE_DIR, 'Doc', 'Doc_Proj_Map.odt')
ODT_BACKUP  = ODT_PATH.replace('.odt', '_backup.odt')

from odf.opendocument import load
from odf.text import P, Span
from odf.draw import Frame, Image
from odf.style import (PageLayout, PageLayoutProperties, MasterPage,
                       Style, GraphicProperties, ParagraphProperties)
from PIL import Image as PILImage

# ── Parâmetros A4 landscape ───────────────────────────────────────────────────
# A4 landscape = 29.7 x 21 cm ; margens 1.5cm todos os lados
MARGIN      = 1.5
PAGE_W_CM   = 29.7
PAGE_H_CM   = 21.0
USABLE_W    = PAGE_W_CM - 2 * MARGIN   # 26.7 cm
USABLE_H    = PAGE_H_CM - 2 * MARGIN   # 18.0 cm

IMG_W_CM = USABLE_W
with PILImage.open(DIAGRAM_IMG) as im:
    pw, ph = im.size
img_h_cm   = round(IMG_W_CM * ph / pw, 3)
TITLE_H_CM = 1.0
space_top  = max(0.0, round((USABLE_H - TITLE_H_CM - img_h_cm) / 2.0, 3))

print(f'Diagrama: {pw}x{ph}px  →  {IMG_W_CM:.2f}cm x {img_h_cm:.3f}cm')
print(f'Espaço acima da imagem: {space_top:.3f}cm  (útil: {USABLE_H}cm)')

# ── Carregar documento ────────────────────────────────────────────────────────
print('Carregando documento...')
shutil.copy2(ODT_PATH, ODT_BACKUP)
doc  = load(ODT_PATH)
body = doc.text

# ── Page layout PAISAGEM ──────────────────────────────────────────────────────
pg_layout = PageLayout(name='PgLayoutLandscape')
pg_layout.addElement(PageLayoutProperties(
    pagewidth=f'{PAGE_W_CM}cm',
    pageheight=f'{PAGE_H_CM}cm',
    printorientation='landscape',
    margintop=f'{MARGIN}cm',
    marginbottom=f'{MARGIN}cm',
    marginleft=f'{MARGIN}cm',
    marginright=f'{MARGIN}cm',
))
doc.automaticstyles.addElement(pg_layout)

# ── Master page PAISAGEM ──────────────────────────────────────────────────────
master_pg = MasterPage(name='MasterLandscape', pagelayoutname='PgLayoutLandscape')
doc.masterstyles.addElement(master_pg)

# ── Estilos de parágrafo ──────────────────────────────────────────────────────
# Heading do capítulo — dispara a virada de página para landscape
chap_style = Style(name='DBChapLandscape', family='paragraph', parentstylename='P125',
                   masterpagename='MasterLandscape')
chap_style.addElement(ParagraphProperties(
    breakbefore='page',
    textalign='center',
    margintop='0cm',
    marginbottom='0.4cm',
))
doc.automaticstyles.addElement(chap_style)

# Título "Diagrama" dentro da página
diag_title_style = Style(name='DBDiagTitleLS', family='paragraph', parentstylename='P125')
diag_title_style.addElement(ParagraphProperties(
    textalign='center',
    margintop='0cm',
    marginbottom='0.2cm',
))
doc.automaticstyles.addElement(diag_title_style)

# Parágrafo da imagem (com espaço para centralizar verticalmente)
img_para_style = Style(name='DBImgParaLS', family='paragraph', parentstylename='P125')
img_para_style.addElement(ParagraphProperties(
    textalign='center',
    margintop=f'{space_top:.3f}cm',
    marginbottom='0cm',
))
doc.automaticstyles.addElement(img_para_style)

# Estilo de frame inline
frame_style = Style(name='DiagramFrameLS', family='graphic')
frame_style.addElement(GraphicProperties(
    wrap='none',
    runthrough='foreground',
    horizontalpos='from-left',
    horizontalrel='paragraph',
    verticalpos='top',
    verticalrel='baseline',
))
doc.automaticstyles.addElement(frame_style)

# ── Registrar imagem ──────────────────────────────────────────────────────────
img_href = doc.addPicture(
    'Pictures/er_diagram_ls.png', 'image/png',
    open(DIAGRAM_IMG, 'rb').read()
)

# ── Nós do capítulo ───────────────────────────────────────────────────────────
# "9.) Banco De Dados" — também aciona a virada de página para landscape
p_chapter = P(stylename='DBChapLandscape')
sp = Span(stylename='T93')
sp.addText('9')
p_chapter.addElement(sp)
p_chapter.addText('.) Banco De Dados')

# "Diagrama"
p_diag_title = P(stylename='DBDiagTitleLS')
sp2 = Span(stylename='T93')
sp2.addText('Diagrama')
p_diag_title.addElement(sp2)

# Frame com imagem
frame = Frame(
    stylename=frame_style,
    name='DiagramaERLS',
    anchortype='as-char',
    width=f'{IMG_W_CM}cm',
    height=f'{img_h_cm}cm',
    zindex='200',
)
frame.addElement(Image(href=img_href, type='simple', show='embed', actuate='onLoad'))

p_img = P(stylename='DBImgParaLS')
p_img.addElement(frame)

# ── Adicionar ao body ─────────────────────────────────────────────────────────
body.addElement(p_chapter)
body.addElement(p_diag_title)
body.addElement(p_img)
body.addElement(P(stylename='P125'))

# ── Salvar ────────────────────────────────────────────────────────────────────
doc.save(ODT_PATH)
print(f'Salvo: {ODT_PATH}')
print('Capitulo "Banco De Dados" em PAISAGEM adicionado com sucesso!')
