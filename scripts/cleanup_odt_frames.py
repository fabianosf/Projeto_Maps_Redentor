"""
Remove frames ScreenFig duplicados do ODT (remanescentes de versões anteriores).
Mantém apenas os frames que estão como filhos diretos de parágrafos no body.
"""
import sys, os, shutil, zipfile, re, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ODT_PATH   = r'Doc\Doc_Proj_Map.odt'
TMP_PATH   = ODT_PATH + '.tmp'

with zipfile.ZipFile(ODT_PATH) as zin:
    all_files = {name: zin.read(name) for name in zin.namelist()}

content = all_files['content.xml'].decode('utf-8')

# Contar ocorrências de cada ScreenFig
screen_figs = re.findall(r'draw:name="(ScreenFig\d+)"', content)
print('Frames antes da limpeza:', screen_figs)

# Identificar blocos draw:frame com anchortype="page" (antigos) e remover
# Esses frames têm text:anchor-type="page" e devem ser eliminados
import xml.etree.ElementTree as ET

# Usar regex para remover draw:frame com anchor-type="page" e nome ScreenFig
# Padrão: <draw:frame ... text:anchor-type="page" ... draw:name="ScreenFig..." ...> ... </draw:frame>
# Remover todos os draw:frame page-anchored com ScreenFig
pattern = r'<draw:frame\b[^>]*text:anchor-type="page"[^>]*draw:name="ScreenFig\d+"[^>]*/>'
removed_simple = re.findall(pattern, content)
content_new = re.sub(pattern, '', content)

# Também tentar com atributos em ordem diferente
pattern2 = r'<draw:frame\b[^>]*draw:name="ScreenFig\d+"[^>]*text:anchor-type="page"[^>]*/>'
removed2 = re.findall(pattern2, content_new)
content_new = re.sub(pattern2, '', content_new)

# Tentar padrão com bloco completo (não self-closing)
# <draw:frame ... text:anchor-type="page" ...> ... </draw:frame>
pattern3 = r'<draw:frame\b(?=[^>]*text:anchor-type="page")(?=[^>]*draw:name="ScreenFig)[^>]*>.*?</draw:frame>'
removed3 = re.findall(pattern3, content_new, re.DOTALL)
content_new = re.sub(pattern3, '', content_new, flags=re.DOTALL)

print(f'Removidos (simple): {len(removed_simple)}')
print(f'Removidos (order2): {len(removed2)}')
print(f'Removidos (block):  {len(removed3)}')

screen_figs_after = re.findall(r'draw:name="(ScreenFig\d+)"', content_new)
print('Frames depois da limpeza:', screen_figs_after)

# Salvar ODT limpo
all_files['content.xml'] = content_new.encode('utf-8')
with zipfile.ZipFile(TMP_PATH, 'w', zipfile.ZIP_DEFLATED) as zout:
    # mimetype deve ser primeiro e não comprimido
    zout.writestr(
        zipfile.ZipInfo('mimetype'),
        all_files.get('mimetype', b'application/vnd.oasis.opendocument.text'),
        compress_type=zipfile.ZIP_STORED,
    )
    for name, data in all_files.items():
        if name == 'mimetype':
            continue
        zout.writestr(name, data)

os.replace(TMP_PATH, ODT_PATH)
print('ODT limpo salvo:', ODT_PATH)
