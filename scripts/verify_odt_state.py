import sys, zipfile, os, datetime, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

odt = r'Doc\Doc_Proj_Map.odt'
bak = r'Doc\Doc_Proj_Map_backup.odt'

print('=== DATAS ===')
for f in [odt, bak]:
    if os.path.exists(f):
        ts = os.path.getmtime(f)
        sz = os.path.getsize(f) // 1024
        print('  ' + f + ': ' + str(datetime.datetime.fromtimestamp(ts)) + '  (' + str(sz) + ' KB)')

print()
with zipfile.ZipFile(odt) as z:
    content = z.read('content.xml').decode('utf-8', errors='replace')
    pics = [n for n in z.namelist() if n.startswith('Pictures/')]

print('=== CONTEUDO ===')
print('  Cap 8 (Interface grafica): ' + str('Interface' in content and 'Front End' in content))
print('  Cap 9 (Banco De Dados): ' + str('Banco De Dados' in content))
print('  Pagina Landscape: ' + str('MasterLandscape' in content or 'PgLayoutLandscape' in content))
print('  Imagens embarcadas: ' + str(len(pics)))
for p in pics:
    print('    ' + p)

print()
print('=== TELAS REFERENCIADAS ===')
screens = re.findall(r'Tela \d+[^\<\"]{0,60}', content)
for s in sorted(set(s.strip() for s in screens)):
    print('  ' + s)
