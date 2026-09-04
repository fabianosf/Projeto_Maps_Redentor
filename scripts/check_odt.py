import zipfile, sys, re
sys.stdout.reconfigure(encoding='utf-8')
odt = r'Doc\Doc_Proj_Map.odt'
with zipfile.ZipFile(odt) as z:
    manifest = z.read('META-INF/manifest.xml').decode('utf-8')
    content  = z.read('content.xml').decode('utf-8')
    files    = z.namelist()

man_imgs  = re.findall(r'full-path="(Pictures/[^"]+)"', manifest)
cont_imgs = re.findall(r'xlink:href="(Pictures/[^"]+)"', content)
zip_imgs  = [f for f in files if f.startswith('Pictures/')]

print('Imagens no manifest:', man_imgs)
print('Imagens no content: ', cont_imgs)
print('Imagens no ZIP:     ', zip_imgs)

missing_manifest = set(cont_imgs) - set(man_imgs)
missing_zip      = set(cont_imgs) - set(zip_imgs)
print()
print('Referenciadas no content mas ausentes do manifest:', missing_manifest)
print('Referenciadas no content mas ausentes do ZIP:     ', missing_zip)

# Mostrar um frame gerado para inspecao
frames = re.findall(r'<draw:frame[^>]+>', content)
print()
print('Ultimo frame gerado:')
for f in frames[-3:]:
    print(' ', f)
