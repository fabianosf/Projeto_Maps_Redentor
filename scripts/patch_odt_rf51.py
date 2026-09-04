"""Alinha RF-51 no ODT: após deletar, a tela Guia permanece aberta."""
import re
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ODT = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

RF51_C_OLD = (
    '<text:p text:style-name="P238"><text:s text:c="2"/>'
    '<text:span text:style-name="T153">c.) Fechar a tela</text:span></text:p>'
)
RF51_C_NEW = (
    '<text:p text:style-name="P238"><text:s text:c="2"/>'
    '<text:span text:style-name="T153">c.) A tela da Guia deverá permanecer aberta;</text:span></text:p>'
)

RF51_B_OLD = "informando: “Usuário deletado com sucesso!”;"
RF51_B_NEW = "informando: “Guia excluída com sucesso!”;"


def main() -> None:
    if not ODT.is_file():
        raise SystemExit(f"ODT não encontrado: {ODT}")

    shutil.copy2(ODT, BACKUP)

    with zipfile.ZipFile(ODT, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        other = {name: zin.read(name) for name in zin.namelist() if name != "content.xml"}

    changed = []
    if RF51_C_OLD in content:
        content = content.replace(RF51_C_OLD, RF51_C_NEW, 1)
        changed.append("RF-51-c")
    else:
        print("AVISO: item c.) RF-51 não encontrado (talvez já atualizado).")

    if RF51_B_OLD in content:
        content = content.replace(RF51_B_OLD, RF51_B_NEW, 1)
        changed.append("RF-51-b")

    with zipfile.ZipFile(ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("content.xml", content.encode("utf-8"))
        for name, data in other.items():
            zout.writestr(name, data)

    if changed:
        print(f"ODT atualizado: {', '.join(changed)}")


if __name__ == "__main__":
    main()
