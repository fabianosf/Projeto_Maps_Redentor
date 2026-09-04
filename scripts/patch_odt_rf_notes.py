"""Atualiza notas RF-03 (login) e RF-25 (Configuração) no Doc_Proj_Map.odt."""
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ODT = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

RF03_OLD = (
    '<text:span text:style-name="T94">Ao menos 1(Hum) caracter especial;</text:span>'
    '</text:p><text:p text:style-name="P142"/></table:table-cell>'
)
RF03_NEW = (
    '<text:span text:style-name="T94">Ao menos 1(Hum) caracter especial;</text:span>'
    '</text:p><text:p text:style-name="P142"><text:span text:style-name="T94">'
    'Nota: a validação da política de senha ocorre ao pressionar Confirmar '
    '(mesma regra da Tela 02).</text:span></text:p><text:p text:style-name="P142"/>'
    '</table:table-cell>'
)

RF25_OLD = (
    'o botão “Configuração” não estará visivel na tela;</text:span></text:p>'
)
RF25_NEW = (
    'o botão “Configuração” não estará visível na tela; '
    'o botão “Configuração” será exibido somente para os perfis '
    '“Administrador” e “Inspetor”;</text:span></text:p>'
)


def main() -> None:
    if not ODT.is_file():
        raise SystemExit(f"ODT não encontrado: {ODT}")

    shutil.copy2(ODT, BACKUP)

    with zipfile.ZipFile(ODT, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        other = {name: zin.read(name) for name in zin.namelist() if name != "content.xml"}

    changed = []
    if RF03_OLD in content:
        content = content.replace(RF03_OLD, RF03_NEW, 1)
        changed.append("RF-03")
    else:
        print("AVISO: bloco RF-03 não encontrado (talvez já atualizado).")

    if RF25_OLD in content:
        content = content.replace(RF25_OLD, RF25_NEW, 1)
        changed.append("RF-25")
    else:
        print("AVISO: bloco RF-25 não encontrado (talvez já atualizado).")

    with zipfile.ZipFile(ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("content.xml", content.encode("utf-8"))
        for name, data in other.items():
            zout.writestr(name, data)

    if changed:
        print(f"ODT atualizado: {', '.join(changed)}")
    else:
        print("Nenhuma alteração aplicada.")


if __name__ == "__main__":
    main()
