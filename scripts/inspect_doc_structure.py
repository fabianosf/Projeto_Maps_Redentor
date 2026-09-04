"""
Inspeciona a estrutura do Doc_Proj_Map.odt para localizar o capítulo 8
e verificar onde as telas foram inseridas.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ODT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'Doc', 'Doc_Proj_Map.odt')

from odf.opendocument import load

doc  = load(ODT_PATH)
body = doc.text

def get_text(node):
    parts = []
    for child in node.childNodes:
        if hasattr(child, 'data'):
            parts.append(child.data)
        elif hasattr(child, 'childNodes'):
            parts.append(get_text(child))
    return ''.join(parts)

def qname_local(node):
    if hasattr(node, 'qname'):
        return node.qname[1]
    return '?'

print('=== ESTRUTURA DO BODY (últimos 80 nós) ===')
children = list(body.childNodes)
print(f'Total de filhos diretos: {len(children)}')
print()

# Mostrar últimos 80 nós para ver onde as telas estão
start = max(0, len(children) - 80)
for i, node in enumerate(children[start:], start=start):
    local = qname_local(node)
    txt   = get_text(node).strip()[:70]

    # Verificar se tem frame dentro
    has_frame = False
    frame_name = ''
    for child in getattr(node, 'childNodes', []):
        if qname_local(child) == 'frame':
            has_frame = True
            frame_name = child.getAttribute('name') or ''
            break

    if has_frame:
        print(f'  [{i:3d}] <{local}> [FRAME: {frame_name}]')
    elif txt:
        print(f'  [{i:3d}] <{local}> "{txt}"')
    else:
        print(f'  [{i:3d}] <{local}> (vazio)')

print()
print('=== CAPÍTULOS IDENTIFICADOS (text:h e P com número) ===')
for i, node in enumerate(children):
    local = qname_local(node)
    txt   = get_text(node).strip()
    if local in ('h',) or (local == 'p' and txt and txt[0].isdigit() and '.)' in txt[:5]):
        print(f'  [{i:3d}] <{local}> "{txt[:80]}"')
