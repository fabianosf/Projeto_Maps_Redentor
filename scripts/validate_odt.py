import zipfile, sys, re, xml.etree.ElementTree as ET, os, shutil
sys.stdout.reconfigure(encoding='utf-8')
odt = r'Doc\Doc_Proj_Map.odt'
with zipfile.ZipFile(odt) as z:
    content = z.read('content.xml').decode('utf-8')
    ET.fromstring(content)
    frames  = re.findall(r'draw:name="(ScreenFig\d+)"', content)
    anchors = re.findall(r'text:anchor-type="(\w+)"', content)
    hpos    = re.findall(r'style:horizontal-pos="([^"]+)"', content)
    vpos    = re.findall(r'style:vertical-pos="([^"]+)"', content)
    hrel    = re.findall(r'style:horizontal-rel="([^"]+)"', content)
    vrel    = re.findall(r'style:vertical-rel="([^"]+)"', content)
    pics    = [n for n in z.namelist() if 'tela_' in n]

print('XML valido')
print('Frames:        ', frames)
print('Anchor types:  ', set(anchors))
print('Horizontal-pos:', set(hpos))
print('Vertical-pos:  ', set(vpos))
print('Horizontal-rel:', set(hrel))
print('Vertical-rel:  ', set(vrel))
print('Imagens no ZIP:', pics)
shutil.copy2(odt, odt.replace('.odt', '_backup.odt'))
print('Backup OK:', os.path.getsize(odt.replace('.odt', '_backup.odt')), 'bytes')
