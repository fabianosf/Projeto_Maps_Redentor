"""Atualiza RN-03 no Doc_Proj_Map.odt com a matriz de perfis."""
import re
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ODT = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

# Bloco exato da célula RN-03 (entre código RN-03 e linha RN-04 / item 04).
RN03_CELL_PATTERN = re.compile(
    r'(<table:table-cell table:style-name="Tabela2\.C2" office:value-type="string">'
    r'<text:p text:style-name="P130"><text:s/><text:span text:style-name="T95">)'
    r'.*?'
    r'(</text:span></text:p></table:table-cell></table:table-row>'
    r'<table:table-row><table:table-cell table:style-name="Tabela2\.A2" '
    r'office:value-type="string"><text:p text:style-name="P131">04</text:p>)',
    re.S,
)

RN03_NEW_BODY = (
    "Matriz de acesso por perfil:</text:span></text:p>"
    '<text:p text:style-name="P130"/>'
    '<text:p text:style-name="P130">'
    '<text:span text:style-name="T96">a.) Perfil “Administrador”: '
    "acesso a todas as funcionalidades da aplicação;</text:span></text:p>"
    '<text:p text:style-name="P130">'
    '<text:span text:style-name="T96">b.) Perfil “Inspetor”: '
    "acesso a todas as funcionalidades, exceto o botão “Reset” de senha "
    "na Tela 03 — Cadastro de Usuário (o botão deverá permanecer "
    "desabilitado para este perfil);</text:span></text:p>"
    '<text:p text:style-name="P130">'
    '<text:span text:style-name="T96">c.) Perfil “Despachante”: '
    "acesso a todas as funcionalidades operacionais, exceto a Tela 09 — "
    "Configuração (sem acesso à área de configuração da aplicação);</text:span></text:p>"
    '<text:p text:style-name="P130"/>'
    '<text:p text:style-name="P130">'
    '<text:span text:style-name="T96">Nota: a Tela 09 — Configuração '
    "será exibida somente para os perfis “Administrador” e “Inspetor”."
)


def main() -> None:
    if not ODT.is_file():
        raise SystemExit(f"ODT não encontrado: {ODT}")

    shutil.copy2(ODT, BACKUP)

    with zipfile.ZipFile(ODT, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        other = {name: zin.read(name) for name in zin.namelist() if name != "content.xml"}

    match = RN03_CELL_PATTERN.search(content)
    if not match:
        raise SystemExit("Bloco RN-03 não encontrado no content.xml.")

    old_inner = match.group(0)
    new_cell = f"{match.group(1)}{RN03_NEW_BODY}{match.group(2)}"
    content = content.replace(old_inner, new_cell, 1)

    with zipfile.ZipFile(ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("content.xml", content.encode("utf-8"))
        for name, data in other.items():
            zout.writestr(name, data)

    print("ODT atualizado: RN-03 (matriz de perfis).")


if __name__ == "__main__":
    main()
