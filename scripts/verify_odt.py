import zipfile, sys, re
sys.stdout.reconfigure(encoding='utf-8')
odt_path = r'Doc\Doc_Proj_Map.odt'
with zipfile.ZipFile(odt_path) as z:
    pics = [n for n in z.namelist() if 'screen_' in n]
    print('Novas imagens:')
    for p in pics:
        info = z.getinfo(p)
        print(f'  {p}  ({info.file_size//1024} KB)')
    
    content = z.read('content.xml').decode('utf-8')
    
# Verificar presença das telas no XML
frames = re.findall(r'ScreenFig\d+', content)
print()
print('Frames inseridos:', frames)

titles = re.findall(r'Tela \d+[^\<]{0,40}', content)
print()
print('Titulos encontrados:')
for t in titles[:20]:
    print(' ', t)
