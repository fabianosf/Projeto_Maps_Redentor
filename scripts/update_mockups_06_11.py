"""
Re-gera apenas os mockups das telas 06 e 11 modificadas,
depois executa o rebuild do capitulo 8.
"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS_DIR   = os.path.join(BASE_DIR, 'screenshots')
MOCKUPS_DIR = os.path.join(SHOTS_DIR, 'mockups')

from PIL import Image, ImageDraw

BEZEL_SIDE   = 28
BEZEL_TOP    = 90
BEZEL_BOTTOM = 70
CORNER_R     = 36
BODY_COLOR   = (24, 24, 28)
BEZEL_COLOR  = (50, 50, 55)
CAM_COLOR    = (8, 8, 10)

def make_mockup(screen_path, out_path):
    screen = Image.open(screen_path).convert('RGBA')
    sw, sh = screen.size
    fw = sw + 2 * BEZEL_SIDE
    fh = sh + BEZEL_TOP + BEZEL_BOTTOM
    phone = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(phone)
    draw.rounded_rectangle([(0,0),(fw-1,fh-1)], radius=CORNER_R,
                            fill=BODY_COLOR+(255,), outline=BEZEL_COLOR+(255,), width=3)
    sx, sy = BEZEL_SIDE, BEZEL_TOP
    draw.rectangle([(sx,sy),(sx+sw-1,sy+sh-1)], fill=(255,255,255,255))
    cam_cx = fw // 2
    cam_cy = BEZEL_TOP // 2
    cam_r  = 8
    draw.ellipse([(cam_cx-cam_r, cam_cy-cam_r),(cam_cx+cam_r, cam_cy+cam_r)], fill=CAM_COLOR+(255,))
    phone.paste(screen, (sx, sy), screen)
    phone.save(out_path, 'PNG')
    print(f'  Mockup: {os.path.basename(out_path)} ({fw}x{fh})')

TARGET_FILES = ['04_cadastro_mapa.png', '13_configuracao.png']
for fname in TARGET_FILES:
    src = os.path.join(SHOTS_DIR, fname)
    dst = os.path.join(MOCKUPS_DIR, fname)
    if os.path.exists(src):
        make_mockup(src, dst)
    else:
        print(f'  [SKIP] {fname} nao encontrado em {SHOTS_DIR}')

print('Mockups atualizados. Reconstruindo capitulo 8...')
import subprocess
result = subprocess.run(
    [sys.executable, os.path.join(BASE_DIR, 'scripts', 'rebuild_odt_ch8.py')],
    capture_output=False
)
sys.exit(result.returncode)
