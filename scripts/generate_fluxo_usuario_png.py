# -*- coding: utf-8 -*-
"""Gera fluxogramas RedMapa com visual 3D profissional (páginas 19–21)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parents[1]
OUT_LOGIN = BASE / "Doc" / "images" / "fluxo-operacional-login.png"
OUT_OPERACOES = BASE / "Doc" / "images" / "fluxo-usuario-operacoes.png"
OUT_ADMIN = BASE / "Doc" / "images" / "fluxo-usuario-admin.png"
OUT_LOGIN.parent.mkdir(parents=True, exist_ok=True)

# Superamostragem para antialiasing nítido no documento
SCALE = 3
# Escala global do fluxograma (+10% — fontes, caixas e espaçamentos)
FLOW_SIZE_SCALE = 1.16


def _f(v: float) -> int:
    return int(round(v * FLOW_SIZE_SCALE))

BG = (255, 255, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
BLUE = (0, 69, 135)  # primary #004587
LINE = (51, 71, 92)
BTN_TEXT = (15, 23, 42)  # slate-900 — texto dos botões actionBtn3d

# actionBtn3d.ts — botões das telas (Login, GUIA, Confirmar, etc.)
BTN_GRAD_TOP = (200, 214, 232)   # #C8D6E8
BTN_GRAD_MID = (176, 196, 222)   # #B0C4DE
BTN_GRAD_BOT = (143, 168, 201)   # #8FA8C9
BTN_BORDER = (154, 171, 196)     # #9AABC4
BTN_RADIUS = _f(8)                 # rounded-lg / theme.radius.button

# Losangos de decisão (mantêm visual distinto)
DEC = {
    "front_top": (255, 243, 199),
    "front_bot": (252, 211, 77),
    "side": (217, 145, 32),
    "bottom": (180, 113, 20),
    "edge": (133, 77, 14),
    "hi": (255, 255, 255),
}

DEPTH_X = 11
DEPTH_Y = 8
SHADOW_BLUR = 5
SHADOW_ALPHA = 58
BTN_DROP_SHADOW_Y = 6
BTN_DROP_SHADOW_BLUR = 7
BTN_DROP_SHADOW_ALPHA = 56  # rgba(15,23,42,0.22)


_FONT_CACHE: dict[tuple[int, bool], ImageFont.ImageFont] = {}
_FONT_PATHS: dict[bool, str] = {}


def _font_path(bold: bool) -> str | None:
    if bold in _FONT_PATHS:
        return _FONT_PATHS[bold]
    candidates = [
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            ImageFont.truetype(path, 12)
            _FONT_PATHS[bold] = path
            return path
        except OSError:
            continue
    _FONT_PATHS[bold] = ""
    return None


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    path = _font_path(bold)
    if path:
        fnt = ImageFont.truetype(path, size)
    else:
        fnt = ImageFont.load_default()
    _FONT_CACHE[key] = fnt
    return fnt


def scaled_font(fnt: ImageFont.ImageFont, scale: int) -> ImageFont.ImageFont:
    size = int(getattr(fnt, "size", 18) * scale)
    path = getattr(fnt, "path", None) or _font_path(True)
    if path:
        return font(size, True)
    return fnt


def draw_len(text: str, fnt: ImageFont.ImageFont) -> float:
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    return tmp.textlength(text, font=fnt)


def wrap_lines(text: str, fnt: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw_len(trial, fnt) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def lerp(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def crop_to_content(img: Image.Image, bg: tuple[int, int, int] = BG, pad: int = 10) -> Image.Image:
    rgb = img.convert("RGB")
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
    bbox = diff.getbbox()
    if not bbox:
        return img
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(img.width, x2 + pad)
    y2 = min(img.height, y2 + pad)
    return img.crop((x1, y1, x2, y2))


# Largura mínima de exportação (2× canvas lógico 1200 px) — centraliza H em todas as páginas
EXPORT_CANVAS_W = _f(2400)


def finalize_flow_image(img: Image.Image, canvas_w: int = EXPORT_CANVAS_W) -> Image.Image:
    """Recorta e centraliza o fluxograma com margens simétricas (H e V)."""
    rgb = img.convert("RGB")
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, BG))
    bbox = diff.getbbox()
    if not bbox:
        return img
    content = rgb.crop(bbox)
    cw, ch = content.size
    pad_v = max(36, int(ch * 0.035))
    total_w = max(canvas_w, cw + 80)
    total_h = ch + 2 * pad_v
    out = Image.new("RGB", (total_w, total_h), BG)
    out.paste(content, ((total_w - cw) // 2, pad_v))
    return out


class FlowCanvas:
    """Canvas RGBA com superamostragem, sombras e extrusão 3D."""

    def __init__(self, w: int, h: int) -> None:
        self.lw, self.lh = w, h
        self.scale = SCALE
        self.img = Image.new("RGBA", (w * SCALE, h * SCALE), (*BG, 255))
        self.shadow = Image.new("RGBA", self.img.size, (0, 0, 0, 0))

    def s(self, v: float) -> int:
        return int(round(v * self.scale))

    def pt(self, xy: tuple[float, float]) -> tuple[int, int]:
        return self.s(xy[0]), self.s(xy[1])

    def _draw(self) -> ImageDraw.ImageDraw:
        return ImageDraw.Draw(self.img)

    def _flush_shadow(self) -> None:
        blurred = self.shadow.filter(
            ImageFilter.GaussianBlur(max(1, BTN_DROP_SHADOW_BLUR * self.scale / 2))
        )
        self.img = Image.alpha_composite(self.img, blurred)
        self.shadow = Image.new("RGBA", self.img.size, (0, 0, 0, 0))

    def _shadow_poly(self, pts: list[tuple[float, float]]) -> None:
        sd = ImageDraw.Draw(self.shadow)
        ox, oy = 4.2, 5.2
        scaled = [self.pt((x + ox, y + oy)) for x, y in pts]
        sd.polygon(scaled, fill=(15, 23, 42, SHADOW_ALPHA))

    def _shadow_round(self, box: tuple[float, float, float, float], radius: float) -> None:
        sd = ImageDraw.Draw(self.shadow)
        ox, oy = 4.2, 5.2
        x1, y1, x2, y2 = box
        sd.rounded_rectangle(
            (self.s(x1 + ox), self.s(y1 + oy), self.s(x2 + ox + DEPTH_X), self.s(y2 + oy + DEPTH_Y)),
            radius=self.s(radius),
            fill=(15, 23, 42, SHADOW_ALPHA),
        )

    def _vertical_gradient_3stop(
        self,
        w: int,
        h: int,
        c_top: tuple[int, int, int],
        c_mid: tuple[int, int, int],
        c_bot: tuple[int, int, int],
    ) -> Image.Image:
        band = Image.new("RGB", (1, h))
        px = band.load()
        last = max(1, h - 1)
        half = last / 2
        for y in range(h):
            if y <= half:
                px[0, y] = lerp(c_top, c_mid, y / max(1, half))
            else:
                px[0, y] = lerp(c_mid, c_bot, (y - half) / max(1, last - half))
        return band.resize((w, h), Image.Resampling.BILINEAR)

    def _paste_gradient_round_3stop(
        self,
        box: tuple[float, float, float, float],
        radius: float,
        c_top: tuple[int, int, int],
        c_mid: tuple[int, int, int],
        c_bot: tuple[int, int, int],
    ) -> None:
        x1, y1, x2, y2 = box
        sx1, sy1, sx2, sy2 = self.s(x1), self.s(y1), self.s(x2), self.s(y2)
        w, h = max(1, sx2 - sx1), max(1, sy2 - sy1)
        grad = self._vertical_gradient_3stop(w, h, c_top, c_mid, c_bot)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=self.s(radius), fill=255)
        self.img.paste(grad, (sx1, sy1), mask)

    def _shadow_button(self, box: tuple[float, float, float, float], radius: float) -> None:
        """Sombra externa: 0 6px 14px rgba(15,23,42,0.22)."""
        sd = ImageDraw.Draw(self.shadow)
        x1, y1, x2, y2 = box
        oy = BTN_DROP_SHADOW_Y
        sd.rounded_rectangle(
            (self.s(x1), self.s(y1 + oy), self.s(x2), self.s(y2 + oy)),
            radius=self.s(radius),
            fill=(15, 23, 42, BTN_DROP_SHADOW_ALPHA),
        )

    def _button_inset_effects(self, box: tuple[float, float, float, float], radius: float) -> None:
        """Inset highlight + inset shadow — mesmo efeito CSS dos botões das telas."""
        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1
        overlay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        inset = 1.5
        # inset 0 2px 4px rgba(255,255,255,0.45)
        od.rounded_rectangle(
            (
                self.s(x1 + inset),
                self.s(y1 + inset),
                self.s(x2 - inset),
                self.s(y1 + min(h * 0.42, 18)),
            ),
            radius=self.s(max(2, radius - 2)),
            fill=(255, 255, 255, 115),
        )
        # inset 0 -4px 7px rgba(70,90,120,0.25)
        od.rounded_rectangle(
            (
                self.s(x1 + inset),
                self.s(y2 - min(h * 0.38, 16)),
                self.s(x2 - inset),
                self.s(y2 - inset),
            ),
            radius=self.s(max(2, radius - 2)),
            fill=(70, 90, 120, 64),
        )
        self.img = Image.alpha_composite(self.img, overlay)

    def action_button_box(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float = BTN_RADIUS,
    ) -> None:
        """Retângulo no estilo actionBtn3d (FrontEnd/src/lib/actionBtn3d.ts)."""
        self._shadow_button((x1, y1, x2, y2), radius)
        self._flush_shadow()
        self._paste_gradient_round_3stop(
            (x1, y1, x2, y2),
            radius,
            BTN_GRAD_TOP,
            BTN_GRAD_MID,
            BTN_GRAD_BOT,
        )
        self._button_inset_effects((x1, y1, x2, y2), radius)
        self._outline_round((x1, y1, x2, y2), radius, BTN_BORDER)

    def _vertical_gradient(
        self,
        w: int,
        h: int,
        c_top: tuple[int, int, int],
        c_bot: tuple[int, int, int],
    ) -> Image.Image:
        band = Image.new("RGB", (1, h))
        px = band.load()
        last = max(1, h - 1)
        for y in range(h):
            px[0, y] = lerp(c_top, c_bot, y / last)
        return band.resize((w, h), Image.Resampling.BILINEAR)

    def _paste_gradient_poly(
        self,
        pts: list[tuple[float, float]],
        c_top: tuple[int, int, int],
        c_bot: tuple[int, int, int],
        bounds: tuple[float, float, float, float],
    ) -> None:
        x1, y1, x2, y2 = bounds
        sx1, sy1, sx2, sy2 = self.s(x1), self.s(y1), self.s(x2), self.s(y2)
        w, h = max(1, sx2 - sx1), max(1, sy2 - sy1)
        grad = self._vertical_gradient(w, h, c_top, c_bot)
        mask = Image.new("L", (w, h), 0)
        local = [(self.s(x) - sx1, self.s(y) - sy1) for x, y in pts]
        ImageDraw.Draw(mask).polygon(local, fill=255)
        self.img.paste(grad, (sx1, sy1), mask)

    def _outline_round(self, box: tuple[float, float, float, float], radius: float, color: tuple[int, int, int]) -> None:
        d = self._draw()
        x1, y1, x2, y2 = box
        d.rounded_rectangle(
            (self.s(x1), self.s(y1), self.s(x2), self.s(y2)),
            radius=self.s(radius),
            outline=color,
            width=max(2, self.scale),
        )

    def _outline_poly(self, pts: list[tuple[float, float]], color: tuple[int, int, int]) -> None:
        d = self._draw()
        d.polygon([self.pt(p) for p in pts], outline=color, width=max(2, self.scale))

    def _highlight_round(self, box: tuple[float, float, float, float], radius: float) -> None:
        x1, y1, x2, y2 = box
        overlay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        inset = 2.2
        od.rounded_rectangle(
            (self.s(x1 + inset), self.s(y1 + inset), self.s(x2 - inset), self.s(y1 + (y2 - y1) * 0.38)),
            radius=self.s(max(2, radius - 2)),
            fill=(255, 255, 255, 72),
        )
        self.img = Image.alpha_composite(self.img, overlay)

    def box_3d(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        palette: dict,
        radius: float = 10,
    ) -> None:
        dx, dy = DEPTH_X, DEPTH_Y
        self._shadow_round((x1, y1, x2, y2), radius)
        self._flush_shadow()
        d = self._draw()
        # Face inferior (chão da extrusão)
        bottom = [(x1, y2), (x2, y2), (x2 + dx, y2 + dy), (x1 + dx, y2 + dy)]
        d.polygon([self.pt(p) for p in bottom], fill=palette["bottom"])
        # Face lateral direita
        side = [(x2, y1), (x2 + dx, y1 + dy), (x2 + dx, y2 + dy), (x2, y2)]
        d.polygon([self.pt(p) for p in side], fill=palette["side"])
        self._paste_gradient_round((x1, y1, x2, y2), radius, palette["front_top"], palette["front_bot"])
        self._highlight_round((x1, y1, x2, y2), radius)
        self._outline_round((x1, y1, x2, y2), radius, palette["edge"])
        d.line([self.pt((x2, y1)), self.pt((x2 + dx, y1 + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((x2, y2)), self.pt((x2 + dx, y2 + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((x1, y2)), self.pt((x1 + dx, y2 + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((x2 + dx, y1 + dy)), self.pt((x2 + dx, y2 + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((x1 + dx, y2 + dy)), self.pt((x2 + dx, y2 + dy))], fill=palette["edge"], width=max(2, self.scale))

    def diamond_3d(self, cx: float, cy: float, r: float, palette: dict) -> None:
        dx, dy = DEPTH_X, DEPTH_Y
        front = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        self._shadow_poly(
            [
                (cx, cy - r),
                (cx + r + dx, cy + dy),
                (cx + dx, cy + r + dy),
                (cx - r, cy),
            ]
        )
        self._flush_shadow()
        d = self._draw()
        right = [(cx + r, cy), (cx + r + dx, cy + dy), (cx + dx, cy + r + dy), (cx, cy + r)]
        bottom = [(cx, cy + r), (cx + dx, cy + r + dy), (cx - r + dx, cy + dy), (cx - r, cy)]
        d.polygon([self.pt(p) for p in right], fill=palette["side"])
        d.polygon([self.pt(p) for p in bottom], fill=palette["bottom"])
        bounds = (cx - r, cy - r, cx + r, cy + r)
        self._paste_gradient_poly(front, palette["front_top"], palette["front_bot"], bounds)
        overlay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        hi = [(cx, cy - r + 4), (cx + r * 0.42, cy - r * 0.22), (cx, cy - 6), (cx - r * 0.42, cy - r * 0.22)]
        od.polygon([self.pt(p) for p in hi], fill=(255, 255, 255, 80))
        self.img = Image.alpha_composite(self.img, overlay)
        self._outline_poly(front, palette["edge"])
        d.line([self.pt((cx + r, cy)), self.pt((cx + r + dx, cy + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((cx, cy + r)), self.pt((cx + dx, cy + r + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((cx - r, cy)), self.pt((cx - r + dx, cy + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((cx + r + dx, cy + dy)), self.pt((cx + dx, cy + r + dy))], fill=palette["edge"], width=max(2, self.scale))
        d.line([self.pt((cx - r + dx, cy + dy)), self.pt((cx + dx, cy + r + dy))], fill=palette["edge"], width=max(2, self.scale))

    def text_block(
        self,
        cx: float,
        cy: float,
        lines: list[str],
        fnt: ImageFont.ImageFont,
        fill: tuple[int, int, int] = DARK,
        line_h: int = 20,
    ) -> None:
        d = self._draw()
        scaled = scaled_font(fnt, self.scale)
        total_h = len(lines) * line_h
        y = cy - total_h / 2
        for line in lines:
            tw = draw_len(line, fnt)
            if fill != BTN_TEXT:
                d.text(self.pt((cx - tw / 2 + 0.4, y + 0.6)), line, fill=(255, 255, 255, 110), font=scaled)
            d.text(self.pt((cx - tw / 2, y)), line, fill=fill, font=scaled)
            y += line_h

    def connect_vertical(
        self,
        x: float,
        y_from: float,
        y_to: float,
        label: str | None = None,
        fsm: ImageFont.ImageFont | None = None,
    ) -> None:
        if y_to <= y_from:
            return
        d = self._draw()
        w = max(3, int(2.2 * self.scale))
        # Sombra da linha
        d.line(
            [self.pt((x + 1.4, y_from)), self.pt((x + 1.4, y_to - 11))],
            fill=(15, 23, 42, 40),
            width=w,
        )
        d.line(
            [self.pt((x, y_from)), self.pt((x, y_to - 11))],
            fill=LINE,
            width=w,
        )
        ah = 13
        aw = 8
        tip = self.pt((x, y_to))
        left = self.pt((x - aw, y_to - ah))
        right = self.pt((x + aw, y_to - ah))
        d.polygon([tip, left, right], fill=LINE)
        if label and fsm:
            self.text_block(x + 22, (y_from + y_to) / 2, [label], fsm, fill=DARK, line_h=LINE_H)

    def connect_horizontal(
        self,
        x_from: float,
        x_to: float,
        y: float,
        label: str | None = None,
        fsm: ImageFont.ImageFont | None = None,
    ) -> None:
        d = self._draw()
        w = max(3, int(2.2 * self.scale))
        ah, aw = 13, 8
        if x_to > x_from:
            d.line([self.pt((x_from, y + 1.4)), self.pt((x_to - 11, y + 1.4))], fill=(15, 23, 42, 40), width=w)
            d.line([self.pt((x_from, y)), self.pt((x_to - 11, y))], fill=LINE, width=w)
            d.polygon(
                [self.pt((x_to, y)), self.pt((x_to - ah, y - aw)), self.pt((x_to - ah, y + aw))],
                fill=LINE,
            )
        else:
            d.line([self.pt((x_from, y + 1.4)), self.pt((x_to + 11, y + 1.4))], fill=(15, 23, 42, 40), width=w)
            d.line([self.pt((x_from, y)), self.pt((x_to + 11, y))], fill=LINE, width=w)
            d.polygon(
                [self.pt((x_to, y)), self.pt((x_to + ah, y - aw)), self.pt((x_to + ah, y + aw))],
                fill=LINE,
            )
        if label and fsm:
            lx = min(x_from, x_to) + 18
            self.text_block(lx, y - 16, [label], fsm, fill=DARK, line_h=LINE_H)

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        d = self._draw()
        w = max(3, int(2.2 * self.scale))
        d.line([self.pt((x1, y1 + 1.4)), self.pt((x2, y2 + 1.4))], fill=(15, 23, 42, 40), width=w)
        d.line([self.pt((x1, y1)), self.pt((x2, y2))], fill=LINE, width=w)

    def finish(self) -> Image.Image:
        rgb = self.img.convert("RGB")
        out_w = self.lw * 2
        out_h = self.lh * 2
        # Exporta em 2× (150 dpi efetivos no documento) a partir de 3×
        return rgb.resize((out_w, out_h), Image.Resampling.LANCZOS)


GAP_CM = 2.0
PX_PER_CM = _f(75)
GAP_PX = int(GAP_CM * PX_PER_CM)
BOX_H_EXTRA = int(0.5 * PX_PER_CM)
BOX_H = _f(54) + BOX_H_EXTRA
TERM_H = _f(50) + BOX_H_EXTRA
DIAMOND_R = _f(66) + int(0.25 * PX_PER_CM)
SIDE_OFFSET = _f(280)
LINE_H = _f(27)
LABEL_FILL = DARK


def terminator(
    c: FlowCanvas,
    cx: int,
    cy: int,
    w: int,
    h: int,
    label: str,
    fnt: ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    c.action_button_box(x1, y1, x2, y2, radius=h // 2)
    c.text_block(cx, cy, wrap_lines(label, fnt, w - 24), fnt, fill=BTN_TEXT, line_h=LINE_H)
    return x1, y1, x2, y2


def process_box(
    c: FlowCanvas,
    cx: int,
    cy: int,
    w: int,
    h: int,
    label: str,
    fnt: ImageFont.ImageFont,
    fill: tuple[int, int, int] | None = None,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    c.action_button_box(x1, y1, x2, y2, radius=BTN_RADIUS)
    c.text_block(cx, cy, wrap_lines(label, fnt, w - 20), fnt, fill=BTN_TEXT, line_h=LINE_H)
    return x1, y1, x2, y2


def decision(
    c: FlowCanvas,
    cx: int,
    cy: int,
    r: int,
    label: str,
    fnt: ImageFont.ImageFont,
    *,
    lines: list[str] | None = None,
    text_max_w: int | None = None,
    line_h: int | None = None,
) -> tuple[int, int, int, int]:
    c.diamond_3d(cx, cy, r, DEC)
    lh = line_h or LINE_H
    if lines is None:
        max_w = text_max_w if text_max_w is not None else r * 2 - 28
        lines = wrap_lines(label, fnt, max_w)
    c.text_block(cx, cy, lines, fnt, line_h=lh)
    return cx - r, cy - r, cx + r, cy + r


def connect_vertical(
    c: FlowCanvas,
    x: int,
    y_from: int,
    y_to: int,
    label: str | None = None,
    fsm: ImageFont.ImageFont | None = None,
) -> None:
    c.connect_vertical(x, y_from, y_to, label, fsm)


def connect_horizontal(
    c: FlowCanvas,
    x_from: int,
    x_to: int,
    y: int,
    label: str | None = None,
    fsm: ImageFont.ImageFont | None = None,
) -> None:
    c.connect_horizontal(x_from, x_to, y, label, fsm)


def return_to_vertical_midpoint(
    c: FlowCanvas,
    side_box: tuple[int, int, int, int],
    cx: int,
    merge_y: int,
) -> None:
    bx = (side_box[0] + side_box[2]) // 2
    c.line(bx, side_box[1], bx, merge_y)
    connect_horizontal(c, bx, cx, merge_y)


def draw_login_flow(
    c: FlowCanvas,
    cx: int,
    y0: int,
    f_body: ImageFont.ImageFont,
    f_label: ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    y = y0

    t1 = terminator(c, cx, y + TERM_H // 2, _f(220), TERM_H, "Início", f_body)
    connect_vertical(c, cx, t1[3], t1[3] + GAP_PX)
    y = t1[3] + GAP_PX + BOX_H // 2
    p1 = process_box(c, cx, y, _f(300), BOX_H, "Executar aplicação", f_body)
    conn_top = p1[3]
    y = conn_top + GAP_PX + BOX_H // 2
    p2 = process_box(c, cx, y, _f(320), BOX_H, "Login: matrícula + senha → Confirmar", f_body)
    conn_bottom = p2[1]
    conn_mid = (conn_top + conn_bottom) // 2
    c.line(cx, conn_top, cx, conn_mid)
    connect_vertical(c, cx, p2[3], p2[3] + GAP_PX)
    y = p2[3] + GAP_PX + DIAMOND_R

    d_troca = decision(c, cx, y, DIAMOND_R, "Trocar senha?", f_body)
    troca_cy = y

    ps_cx = cx + SIDE_OFFSET
    ps = process_box(c, cx + SIDE_OFFSET, troca_cy, _f(190), BOX_H, "Cadastro de Senha", f_body)
    connect_horizontal(c, d_troca[2], ps[0], troca_cy, "Sim", f_label)
    return_to_vertical_midpoint(c, ps, cx, conn_mid)
    connect_vertical(c, cx, conn_mid, conn_bottom)

    connect_vertical(c, cx, d_troca[3], d_troca[3] + GAP_PX, "Não", f_label)
    y = d_troca[3] + GAP_PX + DIAMOND_R

    d_cred = decision(c, cx, y, DIAMOND_R, "Credenciais válidas?", f_body)
    cred_cy = y

    pe_cx = cx - SIDE_OFFSET
    pe = process_box(c, pe_cx, cred_cy, _f(170), BOX_H, "Exibir erro", f_body)
    connect_horizontal(c, d_cred[0], pe[2], cred_cy, "Não", f_label)
    return_to_vertical_midpoint(c, pe, cx, conn_mid)

    connect_vertical(c, cx, d_cred[3], d_cred[3] + GAP_PX, "Sim", f_label)
    y = d_cred[3] + GAP_PX + BOX_H // 2
    p_principal = process_box(c, cx, y, _f(280), BOX_H, "Tela Principal", f_body)
    return p_principal


def generate_login_png() -> None:
    w = _f(900)
    f_body, f_label = _flow_fonts()

    flow_height = (
        TERM_H + GAP_PX + BOX_H + GAP_PX + BOX_H + GAP_PX
        + DIAMOND_R * 2 + GAP_PX + DIAMOND_R * 2 + GAP_PX + BOX_H + _f(56)
    )
    h = flow_height
    cx = w // 2

    canvas = FlowCanvas(w, h)
    y0 = max(_f(24), (h - flow_height) // 2 + _f(12))
    draw_login_flow(canvas, cx, y0, f_body, f_label)
    img = finalize_flow_image(crop_to_content(canvas.finish(), pad=_f(8)))
    img.save(OUT_LOGIN, "PNG", optimize=True)
    print(f"Gerado: {OUT_LOGIN} ({OUT_LOGIN.stat().st_size // 1024} KB)")


REST_GAP = _f(50)
COL_V_GAP_CM = 1.0
COL_V_GAP_PX = int(COL_V_GAP_CM * PX_PER_CM)
COL_STEP = BOX_H + COL_V_GAP_PX
F_BODY = _f(19)
F_LABEL = _f(17)


def _flow_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    return font(F_BODY, True), font(F_LABEL, True)


def generate_operacoes_png() -> None:
    w = _f(1200)
    cx = w // 2
    f_body, _ = _flow_fonts()

    canvas = FlowCanvas(w, _f(2200))

    principal_y = _f(50) + BOX_H // 2
    principal_box = process_box(canvas, cx, principal_y, _f(280), BOX_H, "Tela Principal", f_body)

    cols = [
        ("GUIA", ["Botão GUIA", "Pesquisar guia (NR) ou Novo", "Preencher dados", "Salvar", "Retorno a tela Principal"]),
        (
            "Chegada | Saída",
            [
                "Botão Chegada | Saída",
                "Selecionar linha",
                "Selecionar Guia (Chegada ou Saída)",
                "Preencher dados",
                "Confirmar",
            ],
        ),
        ("Oficina", ["Botão Oficina", "Informar carro", "Avaria + texto (Opcional)", "Confirmar"]),
    ]
    col_spacing = _f(340)
    col_centers = [cx - col_spacing, cx, cx + col_spacing]

    hub_y = principal_box[3] + REST_GAP
    connect_vertical(canvas, cx, principal_box[3], hub_y)
    canvas.line(col_centers[0], hub_y, col_centers[-1], hub_y)

    for col_x, (title, steps) in zip(col_centers, cols, strict=True):
        connect_vertical(canvas, col_x, hub_y, hub_y + REST_GAP)
        canvas.text_block(col_x, hub_y + REST_GAP + _f(16), [title], f_body, fill=BLUE, line_h=LINE_H)
        sy = hub_y + REST_GAP + _f(34) + BOX_H // 2
        for i, step in enumerate(steps):
            box = process_box(canvas, col_x, sy, _f(210), BOX_H, step, f_body)
            if i < len(steps) - 1:
                next_top = sy + BOX_H // 2 + COL_V_GAP_PX
                connect_vertical(canvas, col_x, box[3], next_top)
                sy += COL_STEP
            else:
                sy += COL_STEP

    img = finalize_flow_image(crop_to_content(canvas.finish(), pad=_f(12)))
    img.save(OUT_OPERACOES, "PNG", optimize=True)
    print(f"Gerado: {OUT_OPERACOES} ({OUT_OPERACOES.stat().st_size // 1024} KB)")


def generate_admin_png() -> None:
    w = _f(1200)
    cx = w // 2
    f_body, f_label = _flow_fonts()

    canvas = FlowCanvas(w, _f(1400))

    principal_y = _f(50) + BOX_H // 2
    principal_box = process_box(canvas, cx, principal_y, _f(280), BOX_H, "Tela Principal", f_body)

    admin_diamond_r = DIAMOND_R + int(0.45 * PX_PER_CM)
    d_y = principal_box[3] + GAP_PX + admin_diamond_r
    da = decision(
        canvas,
        cx,
        d_y,
        admin_diamond_r,
        "",
        f_body,
        lines=["Perfil:Administrador|", "Inspetor?"],
        line_h=_f(21),
    )
    connect_vertical(canvas, cx, principal_box[3], da[1])
    connect_horizontal(canvas, da[0], da[0] - _f(100), d_y, "Não", f_label)

    cfg_y = da[3] + GAP_PX + BOX_H // 2
    connect_vertical(canvas, cx, da[3], cfg_y - BOX_H // 2, "Sim", f_label)
    pc = process_box(canvas, cx, cfg_y, _f(280), BOX_H, "Configuração", f_body)

    sub_labels = [
        "Cadastro de usuários",
        "Indicadores",
        "Bloqueio de tentativas",
    ]
    sub_spacing = _f(240)
    sub_centers = [cx - sub_spacing, cx, cx + sub_spacing]

    hub_y = pc[3] + REST_GAP
    connect_vertical(canvas, cx, pc[3], hub_y)
    canvas.line(sub_centers[0], hub_y, sub_centers[-1], hub_y)

    sub_cy = hub_y + REST_GAP + BOX_H // 2
    sub_boxes: list[tuple[int, int, int, int]] = []
    for sub_x, lbl in zip(sub_centers, sub_labels, strict=True):
        connect_vertical(canvas, sub_x, hub_y, sub_cy - BOX_H // 2)
        sub_boxes.append(process_box(canvas, sub_x, sub_cy, _f(210), BOX_H, lbl, f_body))

    merge_y = sub_boxes[0][3] + COL_V_GAP_PX
    for box in sub_boxes:
        bx = (box[0] + box[2]) // 2
        canvas.line(bx, box[3], bx, merge_y)
    canvas.line(sub_centers[0], merge_y, sub_centers[-1], merge_y)

    merge_to_logout_gap = max(REST_GAP, GAP_PX - int(1.0 * PX_PER_CM))
    logout_y = merge_y + merge_to_logout_gap + BOX_H // 2
    connect_vertical(canvas, cx, merge_y, logout_y - BOX_H // 2)
    pl = process_box(canvas, cx, logout_y, _f(280), BOX_H, "Principal → Voltar (logout)", f_body)

    logout_fim_gap = max(REST_GAP, GAP_PX - int(1.0 * PX_PER_CM))
    term_y = pl[3] + logout_fim_gap + TERM_H // 2
    connect_vertical(canvas, cx, pl[3], term_y - TERM_H // 2)
    terminator(canvas, cx, term_y, _f(220), TERM_H, "Fim", f_body)

    img = finalize_flow_image(crop_to_content(canvas.finish(), pad=_f(12)))
    img.save(OUT_ADMIN, "PNG", optimize=True)
    print(f"Gerado: {OUT_ADMIN} ({OUT_ADMIN.stat().st_size // 1024} KB)")


def generate_rest_png() -> None:
    generate_operacoes_png()
    generate_admin_png()


def main() -> None:
    generate_login_png()
    generate_rest_png()


if __name__ == "__main__":
    main()
