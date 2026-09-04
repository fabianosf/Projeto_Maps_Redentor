"""
Reconstrói o capítulo 8 do Doc_Proj_Map.odt:
  - Cada tela em página separada, dentro do capítulo 8
  - Imagem inline (anchor as-char) em parágrafo centralizado
  - Centralização vertical via espaço antes do parágrafo
"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCKUPS_DIR = os.path.join(BASE_DIR, 'screenshots', 'mockups')
ODT_PATH    = os.path.join(BASE_DIR, 'Doc', 'Doc_Proj_Map.odt')
ODT_BACKUP  = ODT_PATH.replace('.odt', '_backup.odt')

from odf.opendocument import load
from odf.text import P, Span
from odf.draw import Frame, Image, TextBox
from odf.style import Style, GraphicProperties, ParagraphProperties
from odf.namespaces import FONS
from PIL import Image as PILImage

IMG_W_CM = 5.486  # 5.225 * 1.05
PAGE_USABLE_W = 16.0
PAIR_GAP_CM = 2.0
PAIR_IMG_W_CM = round((PAGE_USABLE_W - PAIR_GAP_CM) / 2.0, 3)

# A4 com margens 2.5cm: útil 16cm × 24.7cm
PAGE_USABLE_H = 24.7

TELAS = [
    ('01_login.png',              'Tela 01 - Login'),
    ('02_cadastro_senha.png',     'Tela 02 - Cadastro de Senha'),
    ('11_usuarios.png',           'Tela 03 - Cadastro de Usuario'),
    ('10_principal.png',          'Tela 04 - Principal (RedMapa)'),
    ('14_entrada_saida.png',      'Tela 05 - Chegada | Saida (Chegada)'),
    ('15_entrada_saida_saida.png','Tela 06 - Chegada | Saida (Saida)'),
    ('17_mensagem.png',           'Tela 07 - Mensagem'),
    ('16_guia.png',               'Tela 08 - Guia'),
    ('13_configuracao.png',       'Tela 09 - Configuracao'),
    ('18_indicadores.png',        'Tela 10 - Indicadores'),
]

# ── Carregar e backup ─────────────────────────────────────────────────────────
print('Carregando documento...')
shutil.copy2(ODT_PATH, ODT_BACKUP)
doc  = load(ODT_PATH)
body = doc.text

# ── Estilos automáticos ───────────────────────────────────────────────────────

# Estilo de frame inline (as-char): sem wrap, sem bordas
inline_frame_style = Style(name='InlineScreenFrame', family='graphic')
inline_frame_style.addElement(GraphicProperties(
    wrap='none',
    runthrough='foreground',
    horizontalpos='from-left',
    horizontalrel='paragraph',
    verticalpos='top',
    verticalrel='baseline',
))
doc.automaticstyles.addElement(inline_frame_style)

# Estilo de parágrafo: centralizado + quebra de página + espaço acima para centralizar verticalmente
def make_img_para_style(name, space_before_cm, add_page_break=False):
    s = Style(name=name, family='paragraph', parentstylename='P125')
    pp_attrs = {
        'textalign': 'center',
        'marginbottom': '0cm',
        'margintop': f'{space_before_cm:.3f}cm',
    }
    if add_page_break:
        pp_attrs['breakbefore'] = 'page'
    s.addElement(ParagraphProperties(**pp_attrs))
    return s

# Estilos de título de tela (com quebra de página, sem espaço extra)
title_style = Style(name='ScreenTitleStyle', family='paragraph', parentstylename='P125')
title_style.addElement(ParagraphProperties(
    breakbefore='page',
    textalign='center',
    margintop='0cm',
    marginbottom='0.3cm',
))
doc.automaticstyles.addElement(title_style)

inline_frame_gap_style = Style(name='InlineScreenFrameGap', family='graphic')
inline_frame_gap_style.addElement(GraphicProperties(
    wrap='none',
    runthrough='foreground',
    horizontalpos='from-left',
    horizontalrel='paragraph',
    verticalpos='top',
    verticalrel='baseline',
    marginleft=f'{PAIR_GAP_CM}cm',
))
doc.automaticstyles.addElement(inline_frame_gap_style)

pair_title_style = Style(name='ScreenPairTitleStyle', family='paragraph', parentstylename='P125')
pair_title_style.addElement(ParagraphProperties(
    breakbefore='page',
    textalign='center',
    margintop='0cm',
    marginbottom='0.3cm',
))
doc.automaticstyles.addElement(pair_title_style)

pair_title_left_style = Style(name='ScreenPairTitleLeft', family='paragraph', parentstylename='P125')
pair_title_left_style.addElement(ParagraphProperties(
    textalign='right',
    margintop='0cm',
    marginbottom='0.2cm',
    marginright=f'{PAIR_GAP_CM / 2}cm',
))
doc.automaticstyles.addElement(pair_title_left_style)

pair_title_right_style = Style(name='ScreenPairTitleRight', family='paragraph', parentstylename='P125')
pair_title_right_style.addElement(ParagraphProperties(
    textalign='left',
    margintop='0cm',
    marginbottom='0.2cm',
    marginleft=f'{PAIR_GAP_CM / 2}cm',
))
doc.automaticstyles.addElement(pair_title_right_style)


def img_height_cm(img_path, width_cm):
    with PILImage.open(img_path) as im:
        pw, ph = im.size
    return round(width_cm * ph / pw, 3)


def add_picture_frame(doc, fname, img_path, fig_name, width_cm, height_cm, frame_style=None):
    img_href = doc.addPicture(
        f'Pictures/tela_{fname}', 'image/png',
        open(img_path, 'rb').read()
    )
    frame = Frame(
        stylename=frame_style or inline_frame_style,
        name=fig_name,
        anchortype='as-char',
        width=f'{width_cm}cm',
        height=f'{height_cm}cm',
    )
    frame.addElement(Image(
        href=img_href, type='simple', show='embed', actuate='onLoad'
    ))
    return frame


def insert_screen_pair(body, doc, pair_idx, left, right):
    left_fname, left_title = left
    right_fname, right_title = right
    left_path = os.path.join(MOCKUPS_DIR, left_fname)
    right_path = os.path.join(MOCKUPS_DIR, right_fname)
    if not os.path.exists(left_path) or not os.path.exists(right_path):
        print(f'  [SKIP] par {left_fname} / {right_fname}')
        return

    left_h = img_height_cm(left_path, PAIR_IMG_W_CM)
    right_h = img_height_cm(right_path, PAIR_IMG_W_CM)
    img_h = max(left_h, right_h)

    title_h = 1.2
    space_top = max(0.0, round((PAGE_USABLE_H - title_h - img_h) / 2.0, 3))

    pair_titles_style = Style(name=f'ScreenPairTitles{pair_idx:02d}', family='paragraph', parentstylename='P125')
    pair_titles_style.addElement(ParagraphProperties(
        breakbefore='page',
        textalign='center',
        margintop=f'{space_top:.3f}cm',
        marginbottom='0.2cm',
    ))
    doc.automaticstyles.addElement(pair_titles_style)

    p_titles = P(stylename=f'ScreenPairTitles{pair_idx:02d}')
    p_titles.addText(left_title)
    gap_chars = ' ' * 8
    p_titles.addText(gap_chars)
    p_titles.addText(right_title)
    body.addElement(p_titles)

    pair_img_style = Style(name=f'ScreenPairImg{pair_idx:02d}', family='paragraph', parentstylename='P125')
    pair_img_style.addElement(ParagraphProperties(textalign='center', margintop='0cm', marginbottom='0cm'))
    doc.automaticstyles.addElement(pair_img_style)

    left_frame = add_picture_frame(
        doc, left_fname, left_path, f'ScreenPairFig{pair_idx:02d}L', PAIR_IMG_W_CM, img_h,
    )
    right_frame = add_picture_frame(
        doc, right_fname, right_path, f'ScreenPairFig{pair_idx:02d}R',
        PAIR_IMG_W_CM, img_h, inline_frame_gap_style,
    )

    p_img = P(stylename=f'ScreenPairImg{pair_idx:02d}')
    p_img.addElement(left_frame)
    p_img.addElement(right_frame)
    body.addElement(p_img)

    print(
        f'  OK {left_title} + {right_title}  '
        f'({PAIR_IMG_W_CM}cm x {img_h}cm cada, gap={PAIR_GAP_CM}cm)  space-top={space_top}cm'
    )


# ── Localizar capítulo 8 ──────────────────────────────────────────────────────
def get_text(node):
    parts = []
    for child in node.childNodes:
        if hasattr(child, 'data'):
            parts.append(child.data)
        elif hasattr(child, 'childNodes'):
            parts.append(get_text(child))
    return ''.join(parts)

children = list(body.childNodes)
print(f'Filhos diretos: {len(children)}')

ch8_idx = None
for i, node in enumerate(children):
    if not hasattr(node, 'qname') or node.qname[1] != 'p':
        continue
    txt = get_text(node).strip()
    if 'Interface' in txt and 'Front' in txt and len(txt) < 100:
        ch8_idx = i
        print(f'Cap 8 no indice {i}: "{txt}"')
        break

if ch8_idx is None:
    print('ERRO: capitulo 8 nao encontrado')
    sys.exit(1)

# ── Remover conteúdo antigo do capítulo 8 ────────────────────────────────────
for node in children[ch8_idx:]:
    body.removeChild(node)
print(f'Removidos {len(children) - ch8_idx} nos')

# ── Inserir heading do capítulo 8 ────────────────────────────────────────────
p_heading = P(stylename='P125')
sp = Span(stylename='T93')
sp.addText('8')
p_heading.addElement(sp)
p_heading.addText('.) Interface grafica ( Front End)')
body.addElement(p_heading)
body.addElement(P(stylename='P125'))

# ── Inserir telas ─────────────────────────────────────────────────────────────
screen_idx = 0
for idx, entry in enumerate(TELAS):
    if isinstance(entry, list):
        insert_screen_pair(body, doc, idx + 1, entry[0], entry[1])
        screen_idx += 2
        continue

    fname, titulo = entry
    img_path = os.path.join(MOCKUPS_DIR, fname)
    if not os.path.exists(img_path):
        print(f'  [SKIP] {fname} nao encontrado')
        continue

    img_h_cm = img_height_cm(img_path, IMG_W_CM)

    # Espaço acima para centralizar verticalmente
    # Reservar ~1cm para o título, restante dividido
    title_h   = 1.0
    space_top = max(0.0, round((PAGE_USABLE_H - title_h - img_h_cm) / 2.0, 3))

    # Criar estilo de parágrafo de imagem com espaço específico para esta tela
    img_para_style_name = f'ScreenImgPara{idx+1:02d}'
    img_para_style = Style(name=img_para_style_name, family='paragraph',
                           parentstylename='P125')
    img_para_style.addElement(ParagraphProperties(
        textalign='center',
        margintop=f'{space_top:.3f}cm',
        marginbottom='0cm',
    ))
    doc.automaticstyles.addElement(img_para_style)

    # Parágrafo de título (com quebra de página a partir da 2ª tela)
    p_title = P(stylename='ScreenTitleStyle')
    p_title.addText(titulo)
    body.addElement(p_title)

    frame = add_picture_frame(
        doc, fname, img_path, f'ScreenFig{idx+1:02d}', IMG_W_CM, img_h_cm,
    )

    p_img = P(stylename=img_para_style_name)
    p_img.addElement(frame)
    body.addElement(p_img)

    print(f'  OK {titulo}  ({IMG_W_CM}cm x {img_h_cm}cm)  space-top={space_top}cm')
    screen_idx += 1

# ── Forçar bytes das imagens no pacote ODT (evita cache do LibreOffice) ───────
def collect_tela_fnames(telas_list):
    fnames = []
    for entry in telas_list:
        if isinstance(entry, list):
            fnames.append(entry[0][0])
            fnames.append(entry[1][0])
        else:
            fnames.append(entry[0])
    return fnames


def force_sync_picture_bytes(odt_path, mockups_dir, fnames):
    import zipfile

    updates = {}
    for fname in fnames:
        src = os.path.join(mockups_dir, fname)
        if os.path.isfile(src):
            with open(src, 'rb') as f:
                updates[f'Pictures/tela_{fname}'] = f.read()

    if not updates:
        return

    tmp_path = odt_path + '.tmp'
    with zipfile.ZipFile(odt_path, 'r') as zin, zipfile.ZipFile(tmp_path, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in updates:
                data = updates[item.filename]
                print(f'  SYNC {item.filename} ({len(data)} bytes)')
            zout.writestr(item, data)
    os.replace(tmp_path, odt_path)


# ── Salvar ────────────────────────────────────────────────────────────────────
doc.save(ODT_PATH)
print()
print('Sincronizando PNGs embarcados...')
force_sync_picture_bytes(ODT_PATH, MOCKUPS_DIR, collect_tela_fnames(TELAS))
print()
print(f'Salvo: {ODT_PATH}')
print('Concluido!')
