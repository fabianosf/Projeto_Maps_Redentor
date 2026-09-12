# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Monta PDF do catálogo de telas a partir dos PNGs + manifest.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/catalogo-telas")
    manifest_path = out_dir / "manifest.json"
    pdf_path = out_dir / "RedMapa-catalogo-telas.pdf"
    if not manifest_path.exists():
        print(f"Manifest não encontrado: {manifest_path}")
        return 1

    catalog = json.loads(manifest_path.read_text(encoding="utf-8"))
    page_w, page_h = A4
    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    # Capa
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_w / 2, page_h - 40 * mm, "RedMapa")
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_w / 2, page_h - 52 * mm, "Catálogo de telas do aplicativo")
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        page_w / 2,
        page_h - 62 * mm,
        f"{len(catalog)} telas capturadas (viewport mobile 430×932)",
    )
    y = page_h - 80 * mm
    c.setFont("Helvetica", 10)
    for i, item in enumerate(catalog, 1):
        line = f"{i:02d}. {item['title']}  —  {item['route']}"
        c.drawString(20 * mm, y, line[:95])
        y -= 6 * mm
        if y < 20 * mm:
            c.showPage()
            y = page_h - 20 * mm
            c.setFont("Helvetica", 10)
    c.showPage()

    margin = 12 * mm
    header_h = 14 * mm
    for item in catalog:
        img_path = Path(item["file"])
        if not img_path.exists():
            c.setFont("Helvetica", 12)
            c.drawString(margin, page_h - margin, f"Faltando: {item['title']}")
            c.showPage()
            continue

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, page_h - margin, item["title"])
        c.setFont("Helvetica", 9)
        c.drawString(margin, page_h - margin - 5 * mm, item["route"])

        with Image.open(img_path) as im:
            iw, ih = im.size
        max_w = page_w - 2 * margin
        max_h = page_h - header_h - 2 * margin
        scale = min(max_w / iw, max_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        x = (page_w - draw_w) / 2
        y = page_h - header_h - margin - draw_h
        c.drawImage(
            str(img_path),
            x,
            y,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
            anchor="c",
        )
        c.showPage()

    c.save()
    print(f"PDF gerado: {pdf_path}")
    print(f"Tamanho: {pdf_path.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
