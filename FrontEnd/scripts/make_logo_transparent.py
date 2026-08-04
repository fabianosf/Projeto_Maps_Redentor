"""Remove fundo externo do logo circular — PNG com alpha limpo (máscara circular)."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

SRC = Path(__file__).resolve().parents[1] / "src" / "assets" / "logo-mapa-3d.png"
BAK = Path(__file__).resolve().parents[1] / "src" / "assets" / "logo-mapa-3d-original.png"


def main() -> None:
    if not BAK.exists():
        BAK.write_bytes(SRC.read_bytes())

    img = Image.open(BAK).convert("RGBA")
    w, h = img.size
    px = img.load()

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    samples = [px[x, y][:3] for x, y in corners]
    bg = tuple(sum(c[i] for c in samples) // len(samples) for i in range(3))

    def is_bg(rgb: tuple[int, int, int], threshold: float = 36.0) -> bool:
        return sum((rgb[i] - bg[i]) ** 2 for i in range(3)) ** 0.5 < threshold

    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def try_push(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not visited[y][x]:
            r, g, b, _a = px[x, y]
            if is_bg((r, g, b)):
                visited[y][x] = True
                q.append((x, y))

    for x in range(w):
        try_push(x, 0)
        try_push(x, h - 1)
    for y in range(h):
        try_push(0, y)
        try_push(w - 1, y)

    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            try_push(nx, ny)

    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 0:
                xs.append(x)
                ys.append(y)

    if not xs:
        raise SystemExit("Nenhum pixel opaco restante.")

    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    r_out = max(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in zip(xs, ys))

    # Máscara circular limpa: tudo fora do círculo = transparente
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    # +1 para não cortar a borda azul
    draw.ellipse(
        (cx - r_out - 1, cy - r_out - 1, cx + r_out + 1, cy + r_out + 1),
        fill=255,
    )
    img.putalpha(Image.composite(img.split()[3], Image.new("L", (w, h), 0), mask))

    pad = 2
    minx = max(0, int(cx - r_out) - pad)
    miny = max(0, int(cy - r_out) - pad)
    maxx = min(w - 1, int(cx + r_out) + pad)
    maxy = min(h - 1, int(cy + r_out) + pad)
    cropped = img.crop((minx, miny, maxx + 1, maxy + 1))

    cw, ch = cropped.size
    side = max(cw, ch)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(cropped, ((side - cw) // 2, (side - ch) // 2), cropped)
    out.save(SRC, "PNG")
    print(f"OK {SRC} size={out.size} r={r_out:.1f} bg={bg}")


if __name__ == "__main__":
    main()
