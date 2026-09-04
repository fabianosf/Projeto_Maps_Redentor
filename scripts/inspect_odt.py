import zipfile, re, sys

odt_path = r'Doc\Doc_Proj_Map.odt'
with zipfile.ZipFile(odt_path) as z:
    content = z.read('content.xml').decode('utf-8')

# Images referenced
pics = re.findall(r'xlink:href="(Pictures/[^"]+)"', content)
print('Images referenced:')
for p in pics:
    print(' ', p)

# Find all text:p content to identify chapter headings
paragraphs = re.findall(r'<text:p[^>]*>(.*?)</text:p>', content, re.DOTALL)
print('\nParagraphs containing "Interface" or "8" or "Front":')
for p in paragraphs:
    clean = re.sub(r'<[^>]+>', '', p).strip()
    if 'nterface' in clean or 'Front' in clean or ('8' in clean and len(clean) < 80):
        print(' ', repr(clean[:120]))

# Count total paragraphs
print('\nTotal paragraphs:', len(paragraphs))
print('Content length:', len(content))
