"""
Gera apresentação LibreOffice Impress (ODP) com telas centralizadas.

  - Capa: título "RedMapa"
  - Slides das telas (páginas 14–24 do Doc_Proj_Map.odt)

Saída: E:\\RedMapa.odp
"""
from __future__ import annotations

import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from odf.opendocument import OpenDocumentPresentation
from odf.style import (
    Style,
    MasterPage,
    PageLayout,
    PageLayoutProperties,
    TextProperties,
    GraphicProperties,
    DrawingPageProperties,
    ParagraphProperties,
)
from odf.text import P
from odf.draw import Page, Frame, TextBox, Image
from PIL import Image as PILImage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCKUPS = os.path.join(BASE_DIR, "screenshots", "mockups")
OUT_PATH = r"E:\RedMapa.odp"

TELAS = [
    ("01_login.png", "Tela 01 - Login"),
    ("02_cadastro_senha.png", "Tela 02 - Cadastro de Senha"),
    ("11_usuarios.png", "Tela 03 - Cadastro de Usuario"),
    ("10_principal.png", "Tela 04 - Principal (RedMapa)"),
    ("03_lista_mapa.png", "Tela 05 - Lista de Mapas"),
    ("04_cadastro_mapa.png", "Tela 06 - Cadastro de Mapa"),
    ("05_registros.png", "Tela 07 - Registros do Mapa"),
    ("06_cadastro_registro.png", "Tela 08 - Cadastro de Registro"),
    ("07_viagens.png", "Tela 09 - Viagens"),
    ("08_cadastro_viagem.png", "Tela 10 - Cadastro de Viagem"),
    ("13_configuracao.png", "Tela 11 - Configuracao"),
]

# Widescreen 16:9 landscape (cm) — margens 0 para coordenadas absolutas na página
PAGE_W = 33.867
PAGE_H = 19.05

BG = "#B9C8D4"
TITLE_COLOR = "#0B1F4A"


def add_text_frame(page, stylename, text, x, y, w, h, para_style):
    """Frame de texto com posição absoluta na página."""
    frame = Frame(
        width=f"{w:.3f}cm",
        height=f"{h:.3f}cm",
        x=f"{x:.3f}cm",
        y=f"{y:.3f}cm",
        stylename=stylename,
        anchortype="page",
    )
    tb = TextBox()
    p = P(stylename=para_style)
    p.addText(text)
    tb.addElement(p)
    frame.addElement(tb)
    page.addElement(frame)


def add_image_frame(doc, page, stylename, img_path, x, y, w, h):
    """Frame de imagem com posição absoluta na página."""
    href = doc.addPicture(img_path)
    frame = Frame(
        width=f"{w:.3f}cm",
        height=f"{h:.3f}cm",
        x=f"{x:.3f}cm",
        y=f"{y:.3f}cm",
        stylename=stylename,
        anchortype="page",
    )
    frame.addElement(Image(href=href, type="simple", show="embed", actuate="onLoad"))
    page.addElement(frame)


def make_doc() -> OpenDocumentPresentation:
    doc = OpenDocumentPresentation()

    pl = PageLayout(name="PL_Wide")
    pl.addElement(
        PageLayoutProperties(
            pagewidth=f"{PAGE_W}cm",
            pageheight=f"{PAGE_H}cm",
            printorientation="landscape",
            margintop="0cm",
            marginbottom="0cm",
            marginleft="0cm",
            marginright="0cm",
        )
    )
    doc.automaticstyles.addElement(pl)

    master = MasterPage(name="MasterWide", pagelayoutname="PL_Wide")
    doc.masterstyles.addElement(master)

    dp_bg = Style(name="DP_BG", family="drawing-page")
    dp_bg.addElement(DrawingPageProperties(fill="solid", fillcolor=BG, backgroundsize="full"))
    doc.automaticstyles.addElement(dp_bg)

    cover_title = Style(name="CoverTitle", family="paragraph")
    cover_title.addElement(ParagraphProperties(textalign="center"))
    cover_title.addElement(
        TextProperties(fontsize="54pt", fontweight="bold", color=TITLE_COLOR, fontfamily="Calibri")
    )
    doc.styles.addElement(cover_title)

    cover_sub = Style(name="CoverSub", family="paragraph")
    cover_sub.addElement(ParagraphProperties(textalign="center"))
    cover_sub.addElement(
        TextProperties(fontsize="18pt", color=TITLE_COLOR, fontfamily="Calibri")
    )
    doc.styles.addElement(cover_sub)

    slide_title = Style(name="SlideTitle", family="paragraph")
    slide_title.addElement(ParagraphProperties(textalign="center"))
    slide_title.addElement(
        TextProperties(fontsize="26pt", fontweight="bold", color=TITLE_COLOR, fontfamily="Calibri")
    )
    doc.styles.addElement(slide_title)

    fr_style = Style(name="ImgFrame", family="graphic")
    fr_style.addElement(
        GraphicProperties(
            stroke="none",
            fill="none",
            wrap="none",
            horizontalpos="from-left",
            horizontalrel="page",
            verticalpos="from-top",
            verticalrel="page",
        )
    )
    doc.automaticstyles.addElement(fr_style)

    # ── Capa (texto centralizado no slide) ───────────────────────────────────
    cover = Page(name="capa", masterpagename=master, stylename=dp_bg)
    doc.presentation.addElement(cover)

    title_h = 3.0
    sub_h = 1.2
    block_h = title_h + 0.3 + sub_h
    block_y = (PAGE_H - block_h) / 2

    add_text_frame(
        cover, fr_style, "RedMapa",
        x=0, y=block_y, w=PAGE_W, h=title_h, para_style=cover_title,
    )
    add_text_frame(
        cover, fr_style, "Interface gráfica — Telas da aplicação",
        x=0, y=block_y + title_h + 0.3, w=PAGE_W, h=sub_h, para_style=cover_sub,
    )

    # ── Slides das telas ─────────────────────────────────────────────────────
    # Título no topo; imagem do celular centralizada horizontal e verticalmente
    # no espaço restante abaixo do título.
    title_box_h = 1.5
    top_pad = 0.6
    side_pad = 1.0
    bottom_pad = 0.6

    area_top = top_pad + title_box_h + 0.25
    area_bottom = PAGE_H - bottom_pad
    area_h = area_bottom - area_top
    area_w = PAGE_W - 2 * side_pad

    # Altura máxima do mockup (~70% da área útil para caber bem centralizado)
    max_img_h = area_h * 0.95
    max_img_w = min(area_w * 0.38, 7.2)

    for fname, titulo in TELAS:
        img_path = os.path.join(MOCKUPS, fname)
        if not os.path.exists(img_path):
            print(f"  [SKIP] {fname} não encontrado")
            continue

        with PILImage.open(img_path) as im:
            pw, ph = im.size
        aspect = ph / float(pw)

        img_w = max_img_w
        img_h = img_w * aspect
        if img_h > max_img_h:
            img_h = max_img_h
            img_w = img_h / aspect

        # Centro absoluto do slide (eixo X) e centro da área abaixo do título (eixo Y)
        img_x = (PAGE_W - img_w) / 2
        img_y = area_top + (area_h - img_h) / 2

        page = Page(name=titulo[:40], masterpagename=master, stylename=dp_bg)
        doc.presentation.addElement(page)

        add_text_frame(
            page, fr_style, titulo,
            x=0, y=top_pad, w=PAGE_W, h=title_box_h, para_style=slide_title,
        )
        add_image_frame(doc, page, fr_style, img_path, img_x, img_y, img_w, img_h)
        print(
            f"  OK {titulo}  "
            f"{img_w:.2f}x{img_h:.2f}cm  @ ({img_x:.2f}, {img_y:.2f})"
        )

    return doc


def main() -> None:
    print("Gerando apresentação Impress (telas centralizadas)…")
    doc = make_doc()

    # Fecha arquivo anterior se existir (evita falha se estiver aberto)
    base = OUT_PATH[:-4] if OUT_PATH.lower().endswith(".odp") else OUT_PATH
    for path in (base, OUT_PATH, base + ".odp"):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                print(f"AVISO: não foi possível remover {path}: {e}")

    doc.save(base)
    produced = base if os.path.exists(base) else base + ".odp"
    if produced != OUT_PATH:
        if os.path.exists(OUT_PATH):
            os.remove(OUT_PATH)
        shutil.move(produced, OUT_PATH)

    print(f"Salvo: {OUT_PATH}")
    print("Concluído!")


if __name__ == "__main__":
    main()
