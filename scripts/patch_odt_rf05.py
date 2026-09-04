"""Atualiza RF-05 (Cancelar — Tela 01 Login) — Web e dispositivos móveis."""
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ODT = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

RF05_PREVIOUS = (
    "Caso o botão “Cancelar” seja pressionado, a sessão deverá ser encerrada e "
    "a aba ou guia atual do navegador deverá ser fechada, retornando à aba ou "
    "guia que abriu a atual. Nota (aplicação WEB): o fechamento da aba somente "
    "ocorre quando ela foi aberta por script (window.open); caso contrário, "
    "a aplicação utiliza history.back() como alternativa"
)

RF05_FULL = (
    "Caso o botão “Cancelar” seja pressionado, a sessão deverá ser encerrada e "
    "a aba ou guia atual do navegador deverá ser fechada, retornando à aba ou "
    "guia que abriu a atual. Nota (aplicação WEB): o fechamento da aba somente "
    "ocorre quando ela foi aberta por script (window.open); caso contrário, "
    "a aplicação utiliza history.back() como alternativa. "
    "Nota (dispositivos móveis): em smartphones e tablets a aplicação prioriza "
    "history.back(), pois o navegador normalmente não permite fechar a aba "
    "programaticamente; se permanecer na tela de login, a sessão já estará "
    "encerrada e o usuário deverá fechar manualmente ou usar o botão voltar do sistema."
)


def main() -> None:
    if not ODT.is_file():
        raise SystemExit(f"ODT não encontrado: {ODT}")

    shutil.copy2(ODT, BACKUP)

    with zipfile.ZipFile(ODT, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        other = {name: zin.read(name) for name in zin.namelist() if name != "content.xml"}

    if RF05_PREVIOUS in content:
        content = content.replace(RF05_PREVIOUS, RF05_FULL, 1)
        print("RF-05 atualizado (nota mobile).")
    elif RF05_FULL in content:
        print("RF-05 já contém nota mobile.")
    else:
        print("AVISO: bloco RF-05 não encontrado.")

    with zipfile.ZipFile(ODT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("content.xml", content.encode("utf-8"))
        for name, data in other.items():
            zout.writestr(name, data)


if __name__ == "__main__":
    main()
