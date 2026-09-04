# -*- coding: utf-8 -*-
"""Gera Doc/images/redmapa-arquitetura.png — cadastro de usuários na própria aplicação."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "scripts" / "artifacts" / "redmapa-arquitetura.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1400, 780
BG = (255, 255, 255)
BLUE = (37, 99, 235)
BLUE_LIGHT = (219, 234, 254)
BLUE_DARK = (30, 64, 175)
GRAY = (107, 114, 128)
DARK = (31, 41, 55)
ACCENT = (245, 240, 230)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 3,
    radius: int = 16,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def arrow_h(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y: int,
    x2: int,
    color: tuple[int, int, int],
    label: str,
    f: ImageFont.ImageFont,
    fsm: ImageFont.ImageFont,
) -> None:
    draw.line((x1, y, x2, y), fill=color, width=5)
    draw.polygon([(x2, y), (x2 - 14, y - 8), (x2 - 14, y + 8)], fill=color)
    tw = draw.textlength(label, font=fsm)
    draw.text(((x1 + x2 - tw) / 2, y - 28), label, fill=DARK, font=fsm)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = font(28, True)
    f_head = font(20, True)
    f_body = font(16)
    f_small = font(14)
    f_tiny = font(12)

    d.text((W // 2 - 180, 24), "Arquitetura RedMapa / PROJ_MAP", fill=DARK, font=f_title)

    # --- Cliente WEB ---
    cx1, cy1, cx2, cy2 = 40, 110, 360, 520
    rounded_rect(d, (cx1, cy1, cx2, cy2), ACCENT, BLUE, 3)
    d.text((cx1 + 70, cy1 + 16), "Cliente WEB", fill=BLUE_DARK, font=f_head)
    d.text((cx1 + 24, cy1 + 52), "Smartphone + Browser", fill=DARK, font=f_body)
    d.text((cx1 + 24, cy1 + 82), "HTML • CSS • JavaScript", fill=GRAY, font=f_small)
    d.text((cx1 + 24, cy1 + 108), "Mobile-first (RNF-009)", fill=GRAY, font=f_small)
    d.text((cx1 + 24, cy1 + 150), "Telas:", fill=DARK, font=f_body)
    for i, line in enumerate(
        [
            "• Login / Cadastro de senha",
            "• Tela principal (shell)",
            "• Configuração (Admin)",
            "• Relatórios • MAPA",
        ]
    ):
        d.text((cx1 + 24, cy1 + 178 + i * 26), line, fill=DARK, font=f_small)
    d.text((cx1 + 24, cy2 - 44), "Cadastro de usuários", fill=BLUE_DARK, font=f_small)
    d.text((cx1 + 24, cy2 - 22), "via Tela Configuração", fill=BLUE_DARK, font=f_small)

    # --- BackEnd ---
    bx1, by1, bx2, by2 = 500, 90, 920, 540
    rounded_rect(d, (bx1, by1, bx2, by2), (255, 255, 255), BLUE, 4)
    d.text((bx1 + 130, by1 + 14), "BackEnd Python", fill=BLUE_DARK, font=f_head)

    layers = [
        ("API Layer", "Flask 3.x — /api/v1"),
        ("", "auth/* • users/* (Admin) • map/*"),
        ("Service Layer", "auth_service • user_service • DAL"),
        ("Sessão", "server-side + cookie redmapa_sid"),
    ]
    ly = by1 + 58
    for title, desc in layers:
        rounded_rect(d, (bx1 + 24, ly, bx2 - 24, ly + 78), BLUE_LIGHT, BLUE, 2, 12)
        if title:
            d.text((bx1 + 40, ly + 12), title, fill=BLUE_DARK, font=f_body)
            d.text((bx1 + 40, ly + 38), desc, fill=DARK, font=f_small)
        else:
            d.text((bx1 + 40, ly + 28), desc, fill=DARK, font=f_small)
        ly += 92

    d.text((bx1 + 24, by2 - 36), "INSERT/UPDATE tb_usuario (bcrypt)", fill=GRAY, font=f_tiny)

    # --- MariaDB ---
    mx1, my1, mx2, my2 = 980, 130, 1360, 500
    rounded_rect(d, (mx1, my1, mx2, my2), (248, 250, 252), GRAY, 2)
    d.ellipse((mx1 + 90, my1 + 10, mx2 - 90, my1 + 70), fill=(229, 231, 235), outline=GRAY, width=2)
    d.text((mx1 + 150, my1 + 88), "MariaDB 12.x", fill=DARK, font=f_head)
    d.text((mx1 + 150, my1 + 118), "Banco map", fill=GRAY, font=f_small)
    d.text((mx1 + 60, my1 + 170), "Tabelas principais:", fill=DARK, font=f_body)
    for i, tbl in enumerate(["tb_usuario / tb_perfil", "tb_map", "tb_item_map", "tb_viagem", "cadastros mestres"]):
        d.text((mx1 + 60, my1 + 202 + i * 28), f"• {tbl}", fill=DARK, font=f_small)

    # --- Arrows ---
    arrow_h(d, cx2 + 5, 300, bx1 - 5, BLUE, "HTTPS / JSON REST", f_body, f_small)
    arrow_h(d, bx2 + 5, 300, mx1 - 5, BLUE, "SQL • DAL", f_body, f_small)

    # --- Footer dev ---
    rounded_rect(d, (40, 580, 1360, 730), (243, 244, 246), GRAY, 2)
    d.text((60, 610), "Ambiente de desenvolvimento", fill=DARK, font=f_head)
    d.text(
        (60, 648),
        "Windows 10/11 • localhost:5000 (API) • localhost:3306 (MariaDB)",
        fill=GRAY,
        font=f_body,
    )
    d.text(
        (60, 682),
        "Cadastro de usuários: RedMapa (Admin) → API REST → tb_usuario — sem aplicação externa",
        fill=BLUE_DARK,
        font=f_small,
    )

    img.save(OUT, "PNG", optimize=True)
    print(f"Gerado: {OUT}")


if __name__ == "__main__":
    main()
