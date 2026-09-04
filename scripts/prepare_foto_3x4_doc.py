#!/usr/bin/env python3
"""
Gera foto 3x4 (padrão documentos BR) para mockup da Tela 03.
Usa scripts/mockups/assets/foto_funcionario_doc_source.png quando existir.
"""
from __future__ import annotations

import os
import sys
import urllib.request

from PIL import Image, ImageOps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "scripts", "mockups", "assets")
OUT_PATH = os.path.join(ASSETS_DIR, "foto_funcionario_doc.jpg")
LOCAL_SRC = os.path.join(ASSETS_DIR, "foto_funcionario_doc_source.png")
FALLBACK_URL = "https://randomuser.me/api/portraits/men/75.jpg"

OUT_W, OUT_H = 450, 600
BG_COLOR = (255, 255, 255)


def _baixar_origem(dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(
        FALLBACK_URL,
        headers={"User-Agent": "PROJ_MAP-doc-mockup/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())


def _crop_retrato_3x4(img: Image.Image) -> Image.Image:
    """Recorta centro da imagem na proporção 3:4 (retrato, rosto centralizado)."""
    img = img.convert("RGB")
    w, h = img.size
    target_ratio = 3 / 4

    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        new_h = int(w / target_ratio)
        top = max(0, (h - new_h) // 2 - int(h * 0.04))
        box = (0, top, w, min(h, top + new_h))

    return img.crop(box)


def gerar_foto_3x4() -> str:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    tmp = os.path.join(ASSETS_DIR, "_origem_temp.jpg")

    if os.path.isfile(LOCAL_SRC):
        origem = Image.open(LOCAL_SRC)
    else:
        try:
            _baixar_origem(tmp)
            origem = Image.open(tmp)
        except Exception:
            if os.path.exists(OUT_PATH):
                origem = Image.open(OUT_PATH)
            else:
                raise

    retrato = _crop_retrato_3x4(ImageOps.exif_transpose(origem))
    retrato = retrato.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)

    final = Image.new("RGB", (OUT_W, OUT_H), BG_COLOR)
    final.paste(retrato, (0, 0))
    final.save(OUT_PATH, "JPEG", quality=94, optimize=True)

    if os.path.exists(tmp):
        os.remove(tmp)

    return OUT_PATH


def main() -> int:
    path = gerar_foto_3x4()
    print(f"Foto 3x4 gerada: {path} ({OUT_W}x{OUT_H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
