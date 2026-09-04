# -*- coding: utf-8 -*-
"""
Atualiza seção 9.3 no Doc_Proj_Map.odt:
  - Página dedicada: Fluxo Operacional (Login), centralizado
  - Página seguinte: demais fluxos operacionais
"""

from __future__ import annotations

import copy
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ODT_PATH = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP_PATH = BASE / "Doc" / "Doc_Proj_Map.odt.bak"
IMAGE_LOGIN_SRC = BASE / "Doc" / "images" / "fluxo-operacional-login.png"
IMAGE_LOGIN_ODT = "Pictures/fluxo-operacional-login.png"
IMAGE_OPERACOES_SRC = BASE / "Doc" / "images" / "fluxo-usuario-operacoes.png"
IMAGE_OPERACOES_ODT = "Pictures/fluxo-usuario-operacoes.png"
IMAGE_ADMIN_SRC = BASE / "Doc" / "images" / "fluxo-usuario-admin.png"
IMAGE_ADMIN_ODT = "Pictures/fluxo-usuario-admin.png"
GENERATOR = BASE / "scripts" / "generate_fluxo_usuario_png.py"
SECTION_MARKER = "9.3) Fluxos principais"
INSERT_BEFORE = "8.) Interface grafica"
PAGE_WIDTH_CM = 16.0
MAX_FLOW_IMAGE_WIDTH_CM = 14.5
FLOW_WIDTH_SAFETY = 0.96
LOGIN_IMAGE_WIDTH_CM = 10.5
OPERACOES_IMAGE_WIDTH_CM = 10.5
REST_IMAGE_WIDTH_CM = 10.5
FO_NS = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
STYLE_FLUXO_TITULO = "FluxoCentroTitulo"
STYLE_FLUXO_TITULO_LOGIN = "FluxoCentroTituloLogin"
STYLE_FLUXO_TITULO_OPER = "FluxoCentroTituloOper"
STYLE_FLUXO_TITULO_ADMIN = "FluxoCentroTituloAdmin"
STYLE_FLUXO_SUB = "FluxoCentroSub"
STYLE_FLUXO_FIGURA = "FluxoCentroFigura"
STYLE_FLUXO_PAGINA2 = "FluxoPaginaComplementar"
STYLE_FLUXO_PAGINA3 = "FluxoPaginaAdmin"
STYLE_FLUXO_FRAME = "FluxoFrame"
DRAW_NS = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
}


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def para_text(el: ET.Element) -> str:
    return " ".join("".join(el.itertext()).split())


def make_paragraph(style: str, text: str | None = None) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    p.set(qname("text", "style-name"), style)
    if text:
        p.text = text
    return p


def make_page_break(style: str = "P131") -> ET.Element:
    p = ET.Element(qname("text", "p"))
    p.set(qname("text", "style-name"), style)
    ET.SubElement(p, qname("text", "soft-page-break"))
    return p


def clone_heading(template: ET.Element, title: str) -> ET.Element:
    p = copy.deepcopy(template)
    for child in list(p):
        p.remove(child)
    p.text = title
    return p


PAGE_HEIGHT_CM = 29.7
PAGE_MARGIN_TOP_CM = 2.0
PAGE_MARGIN_BOTTOM_CM = 2.0
USABLE_PAGE_CM = PAGE_HEIGHT_CM - PAGE_MARGIN_TOP_CM - PAGE_MARGIN_BOTTOM_CM
FLUXO_TITLE_BLOCK_CM = 1.35
FLUXO_FIGURE_GAP_CM = 1.0


def fluxo_page_margin_top(fig_height_cm: float) -> float:
    """Margem superior para centralizar título + figura na página."""
    block = FLUXO_TITLE_BLOCK_CM + FLUXO_FIGURE_GAP_CM + fig_height_cm + 0.15
    margin = (USABLE_PAGE_CM - block) / 2
    return max(0.5, round(margin, 2))


def figure_height_cm(path: Path, width_cm: float) -> float:
    from PIL import Image

    with Image.open(path) as im:
        w_px, h_px = im.size
    return width_cm * h_px / w_px


def max_figure_width_cm(path: Path) -> float:
    """Largura máxima (cm) para caber título + figura em uma página."""
    from PIL import Image

    max_fig_h = USABLE_PAGE_CM - FLUXO_TITLE_BLOCK_CM - FLUXO_FIGURE_GAP_CM - 0.15 - 1.0
    with Image.open(path) as im:
        w_px, h_px = im.size
    by_height = max_fig_h * w_px / h_px
    return min(MAX_FLOW_IMAGE_WIDTH_CM, by_height)


def choose_flow_image_width(*paths: Path) -> float:
    """Escolhe largura comum que caiba os três fluxogramas em uma página cada."""
    max_w = min(max_figure_width_cm(p) for p in paths) * FLOW_WIDTH_SAFETY
    return round(max_w, 2)


def flow_page_fits(path: Path, width_cm: float) -> bool:
    block = FLUXO_TITLE_BLOCK_CM + FLUXO_FIGURE_GAP_CM + figure_height_cm(path, width_cm) + 0.15
    return block <= USABLE_PAGE_CM - 1.0


def ensure_fluxo_center_styles(
    root: ET.Element,
    *,
    margin_tops: dict[str, float] | None = None,
) -> None:
    """Estilos centralizados — Calibri; figuras inline (sem sobreposição)."""
    auto = root.find("office:automatic-styles", NS)
    if auto is None:
        auto = ET.SubElement(root, qname("office", "automatic-styles"))
    margin_tops = margin_tops or {}

    def upsert_style(
        name: str,
        *,
        font_pt: str | None = None,
        margin_top: str = "0cm",
        margin_bottom: str = "0cm",
        keep_with_next: bool = False,
        keep_with_previous: bool = False,
        break_before: bool = False,
        center: bool = True,
    ) -> None:
        st = None
        for candidate in auto.findall("style:style", NS):
            if candidate.get(qname("style", "name")) == name:
                st = candidate
                break
        if st is None:
            st = ET.SubElement(auto, qname("style", "style"))
            st.set(qname("style", "name"), name)
            st.set(qname("style", "family"), "paragraph")
        else:
            for child in list(st):
                st.remove(child)
        ppr = ET.SubElement(st, qname("style", "paragraph-properties"))
        if center:
            ppr.set(f"{{{FO_NS}}}text-align", "center")
        ppr.set(f"{{{FO_NS}}}margin-top", margin_top)
        ppr.set(f"{{{FO_NS}}}margin-bottom", margin_bottom)
        if keep_with_next:
            ppr.set(f"{{{FO_NS}}}keep-with-next", "always")
        if keep_with_previous:
            ppr.set(f"{{{FO_NS}}}keep-with-previous", "always")
        if break_before:
            ppr.set(f"{{{FO_NS}}}break-before", "page")
        if font_pt:
            tpr = ET.SubElement(st, qname("style", "text-properties"))
            tpr.set(f"{{{FO_NS}}}font-weight", "bold")
            tpr.set(f"{{{FO_NS}}}font-size", font_pt)
            tpr.set(f"{{{FO_NS}}}font-family", "Calibri")
            tpr.set(f"{{{FO_NS}}}font-name", "Calibri")

    upsert_style(
        STYLE_FLUXO_TITULO,
        font_pt="15pt",
        margin_top="0.4cm",
        margin_bottom="0.05cm",
        keep_with_next=True,
        break_before=True,
    )
    for key, style_name in (
        ("login", STYLE_FLUXO_TITULO_LOGIN),
        ("oper", STYLE_FLUXO_TITULO_OPER),
        ("admin", STYLE_FLUXO_TITULO_ADMIN),
    ):
        upsert_style(
            style_name,
            font_pt="15pt",
            margin_top=f"{margin_tops.get(key, 0.4):.2f}cm",
            margin_bottom="0.05cm",
            keep_with_next=True,
            break_before=True,
        )
    upsert_style(
        STYLE_FLUXO_SUB,
        font_pt="13pt",
        margin_bottom="0cm",
        keep_with_next=True,
    )
    upsert_style(
        STYLE_FLUXO_FIGURA,
        margin_top="1cm",
        margin_bottom="0.1cm",
        center=True,
        keep_with_previous=True,
    )
    upsert_style(
        STYLE_FLUXO_PAGINA2,
        margin_top="0cm",
        margin_bottom="0cm",
        break_before=True,
        center=True,
    )
    upsert_style(
        STYLE_FLUXO_PAGINA3,
        margin_top="0cm",
        margin_bottom="0cm",
        break_before=True,
        center=True,
    )
    upsert_frame_style(auto)


def upsert_frame_style(auto: ET.Element) -> None:
    """Estilo gráfico sem borda na figura embutida."""
    st = None
    for candidate in auto.findall("style:style", NS):
        if candidate.get(qname("style", "name")) == STYLE_FLUXO_FRAME:
            st = candidate
            break
    if st is None:
        st = ET.SubElement(auto, qname("style", "style"))
        st.set(qname("style", "name"), STYLE_FLUXO_FRAME)
        st.set(qname("style", "family"), "graphic")
    else:
        for child in list(st):
            st.remove(child)
        if qname("style", "parent-style-name") in st.attrib:
            del st.attrib[qname("style", "parent-style-name")]
    gpr = ET.SubElement(st, qname("style", "graphic-properties"))
    gpr.set(f"{{{DRAW_NS}}}stroke", "none")
    gpr.set(f"{{{FO_NS}}}border", "none")
    gpr.set(f"{{{FO_NS}}}border-left", "none")
    gpr.set(f"{{{FO_NS}}}border-right", "none")
    gpr.set(f"{{{FO_NS}}}border-top", "none")
    gpr.set(f"{{{FO_NS}}}border-bottom", "none")
    gpr.set(f"{{{FO_NS}}}padding", "0cm")
    gpr.set(f"{{{FO_NS}}}margin", "0cm")
    gpr.set(f"{{{DRAW_NS}}}horizontal-pos", "center")
    gpr.set(f"{{{DRAW_NS}}}horizontal-rel", "paragraph")
    gpr.set(f"{{{DRAW_NS}}}mirror", "none")
    style_ns = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    gpr.set(f"{{{style_ns}}}shadow", "none")
    gpr.set(f"{{{style_ns}}}border-line-width", "0cm")


def make_image_paragraph(
    href: str,
    width_cm: float,
    height_cm: float,
    fig_name: str,
    style: str = STYLE_FLUXO_FIGURA,
) -> ET.Element:
    """Figura inline (as-char) — evita sobreposição de frames flutuantes."""
    p = ET.Element(qname("text", "p"))
    p.set(qname("text", "style-name"), style)
    frame = ET.SubElement(p, qname("draw", "frame"))
    frame.set(qname("draw", "style-name"), STYLE_FLUXO_FRAME)
    frame.set(qname("draw", "name"), fig_name)
    frame.set(qname("text", "anchor-type"), "as-char")
    frame.set(f"{{{DRAW_NS}}}stroke", "none")
    frame.set(qname("svg", "width"), f"{width_cm:.3f}cm")
    frame.set(qname("svg", "height"), f"{height_cm:.3f}cm")
    img = ET.SubElement(frame, qname("draw", "image"))
    img.set(qname("xlink", "href"), href)
    img.set(qname("xlink", "type"), "simple")
    img.set(qname("xlink", "show"), "embed")
    img.set(qname("xlink", "actuate"), "onLoad")
    img.set(qname("draw", "mime-type"), "image/png")
    return p


def add_manifest_entry(manifest_xml: bytes, path: str) -> bytes:
    if path.encode() in manifest_xml:
        return manifest_xml
    root = ET.fromstring(manifest_xml)
    ns = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    entry = ET.Element(f"{{{ns}}}file-entry")
    entry.set(f"{{{ns}}}full-path", path)
    entry.set(f"{{{ns}}}media-type", "image/png")
    root.append(entry)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def png_size_cm(path: Path, width_cm: float) -> tuple[float, float]:
    from PIL import Image

    with Image.open(path) as im:
        w_px, h_px = im.size
    aspect = h_px / w_px
    height_cm = round(width_cm * aspect, 3)
    return width_cm, height_cm


def build_section_nodes(heading_tpl: ET.Element) -> list[ET.Element]:
    login_w, login_h = png_size_cm(IMAGE_LOGIN_SRC, LOGIN_IMAGE_WIDTH_CM)
    oper_w, oper_h = png_size_cm(IMAGE_OPERACOES_SRC, OPERACOES_IMAGE_WIDTH_CM)
    admin_w, admin_h = png_size_cm(IMAGE_ADMIN_SRC, REST_IMAGE_WIDTH_CM)

    intro = (
        "Fluxos principais de uso do RedMapa na perspectiva do usuário. "
        "Símbolos: terminador (início/fim), processo, decisão e setas de fluxo."
    )

    nodes: list[ET.Element] = [
        clone_heading(heading_tpl, "9.3) Fluxos principais de uso (visão do usuário)"),
        make_paragraph("P131"),
        make_paragraph("P87", intro),
        make_paragraph("P88"),
        make_paragraph(STYLE_FLUXO_TITULO_LOGIN, "Fluxo Operacional"),
        make_paragraph(STYLE_FLUXO_SUB, "Login"),
        make_image_paragraph(IMAGE_LOGIN_ODT, login_w, login_h, "FigFluxoLogin"),
        make_paragraph(STYLE_FLUXO_TITULO_OPER, "Fluxo Operacional"),
        make_paragraph(STYLE_FLUXO_SUB, "Principal"),
        make_image_paragraph(IMAGE_OPERACOES_ODT, oper_w, oper_h, "FigFluxoOperacoes"),
        make_paragraph(STYLE_FLUXO_TITULO_ADMIN, "Fluxo Operacional"),
        make_paragraph(STYLE_FLUXO_SUB, "Configuração"),
        make_image_paragraph(IMAGE_ADMIN_ODT, admin_w, admin_h, "FigFluxoAdmin"),
        make_paragraph("P131"),
    ]
    return nodes


def find_section_range(text_el: ET.Element) -> tuple[int | None, int | None]:
    children = list(text_el)
    start = end = None
    for i, child in enumerate(children):
        if child.tag == qname("text", "p") and SECTION_MARKER in para_text(child):
            start = i
        if start is not None and i > start and child.tag == qname("text", "p"):
            if INSERT_BEFORE.lower() in para_text(child).lower():
                end = i
                break
    return start, end


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    for src in (IMAGE_LOGIN_SRC, IMAGE_OPERACOES_SRC, IMAGE_ADMIN_SRC):
        if not src.exists():
            raise FileNotFoundError(src)

    flow_width_cm = choose_flow_image_width(
        IMAGE_LOGIN_SRC,
        IMAGE_OPERACOES_SRC,
        IMAGE_ADMIN_SRC,
    )
    for src, label in (
        (IMAGE_LOGIN_SRC, "Login"),
        (IMAGE_OPERACOES_SRC, "Principal"),
        (IMAGE_ADMIN_SRC, "Configuração"),
    ):
        if not flow_page_fits(src, flow_width_cm):
            raise RuntimeError(
                f"Fluxo {label} não cabe em uma página com largura {flow_width_cm} cm"
            )

    global LOGIN_IMAGE_WIDTH_CM, OPERACOES_IMAGE_WIDTH_CM, REST_IMAGE_WIDTH_CM
    LOGIN_IMAGE_WIDTH_CM = flow_width_cm
    OPERACOES_IMAGE_WIDTH_CM = flow_width_cm
    REST_IMAGE_WIDTH_CM = flow_width_cm

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")
        manifest = zin.read("META-INF/manifest.xml")
        archive = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(content)
    login_w, login_h = png_size_cm(IMAGE_LOGIN_SRC, LOGIN_IMAGE_WIDTH_CM)
    oper_w, oper_h = png_size_cm(IMAGE_OPERACOES_SRC, OPERACOES_IMAGE_WIDTH_CM)
    admin_w, admin_h = png_size_cm(IMAGE_ADMIN_SRC, REST_IMAGE_WIDTH_CM)
    ensure_fluxo_center_styles(
        root,
        margin_tops={
            "login": fluxo_page_margin_top(login_h),
            "oper": fluxo_page_margin_top(oper_h),
            "admin": fluxo_page_margin_top(admin_h),
        },
    )
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    start, end = find_section_range(text_el)
    heading_tpl = None
    for child in text_el.findall("text:p", NS):
        if para_text(child).startswith("9.2)"):
            heading_tpl = child
            break
    if heading_tpl is None:
        raise RuntimeError("Template heading 9.2 não encontrado")

    new_nodes = build_section_nodes(heading_tpl)

    if start is not None and end is not None:
        for child in list(text_el)[start:end]:
            text_el.remove(child)
        insert_at = start
    else:
        insert_at = None
        for i, child in enumerate(list(text_el)):
            if child.tag == qname("text", "p") and INSERT_BEFORE.lower() in para_text(child).lower():
                insert_at = i
                break
        if insert_at is None:
            raise RuntimeError(f"Âncora não encontrada: {INSERT_BEFORE}")

    for offset, node in enumerate(new_nodes):
        text_el.insert(insert_at + offset, node)

    archive["content.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    manifest = add_manifest_entry(manifest, IMAGE_LOGIN_ODT)
    manifest = add_manifest_entry(manifest, IMAGE_OPERACOES_ODT)
    manifest = add_manifest_entry(manifest, IMAGE_ADMIN_ODT)
    archive["META-INF/manifest.xml"] = manifest
    archive[IMAGE_LOGIN_ODT] = IMAGE_LOGIN_SRC.read_bytes()
    archive[IMAGE_OPERACOES_ODT] = IMAGE_OPERACOES_SRC.read_bytes()
    archive[IMAGE_ADMIN_ODT] = IMAGE_ADMIN_SRC.read_bytes()

    temp = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in archive.items():
            zout.writestr(name, data)

    try:
        temp.replace(ODT_PATH)
    except OSError:
        alt = ODT_PATH.with_name("Doc_Proj_Map.updated.odt")
        temp.replace(alt)
        raise SystemExit(f"ODT bloqueado. Salvo em: {alt}") from None

    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    print(f"Largura figuras: {flow_width_cm} cm (título + diagrama em uma página)")
    print("Página dedicada: Fluxo Operacional (Login)")
    print(f"Imagens: {IMAGE_LOGIN_ODT}, {IMAGE_OPERACOES_ODT}, {IMAGE_ADMIN_ODT}")


if __name__ == "__main__":
    main()
