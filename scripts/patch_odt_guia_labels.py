"""Atualiza labels da Tela 08 — Guia no Doc_Proj_Map.odt (cap. 9 requisitos)."""
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ODT = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

REPLACEMENTS = [
    ("horário(Pegada)", "INÍCIO(JORNADA)"),
    ("horário (Pegada)", "INÍCIO(JORNADA)"),
    ("Horário(Pegada)", "INÍCIO(JORNADA)"),
    ("horário(Largada)", "FIM(JORNADA)"),
    ("horário (Largada)", "FIM(JORNADA)"),
    ("Horário(Largada)", "FIM(JORNADA)"),
    ("roleta(Inicial)", "ROLETA 01(INICIAL)"),
    ("Roleta(Inicial)", "ROLETA 01(INICIAL)"),
    ("roleta(Final)", "ROLETA 01(FINAL)"),
    ("Roleta(Final)", "ROLETA 01(FINAL)"),
    ("ROLETA(INICIAL)", "ROLETA 01(INICIAL)"),
    ("ROLETA(FINAL)", "ROLETA 01(FINAL)"),
]


def main() -> None:
    if not ODT.is_file():
        raise SystemExit(f"ODT não encontrado: {ODT}")

    shutil.copy2(ODT, BACKUP)

    with zipfile.ZipFile(ODT, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        other = {name: zin.read(name) for name in zin.namelist() if name != "content.xml"}

    changed = 0
    for old, new in REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            changed += 1

    note = (
        "Nota (Tela 08 — Guia): abaixo dos campos ROLETA 01, a tela exibe "
        "ROLETA 02(INICIAL) e ROLETA 02(FINAL); o campo Observação possui a "
        "mesma altura dos campos de roleta."
    )
    marker = "Tela 08 - Guia"
    if note not in content and marker in content:
        idx = content.find(marker)
        insert_at = content.find("</text:p>", idx)
        if insert_at > 0:
            para = (
                f'<text:p text:style-name="P125"><text:span>{note}</text:span></text:p>'
            )
            content = content[: insert_at + len("</text:p>")] + para + content[insert_at + len("</text:p>") :]
            changed += 1

    with zipfile.ZipFile(ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("content.xml", content.encode("utf-8"))
        for name, data in other.items():
            zout.writestr(name, data)

    print(f"ODT Guia labels: {changed} alteração(ões).")


if __name__ == "__main__":
    main()
