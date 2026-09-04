# -*- coding: utf-8 -*-
"""Insere ou atualiza os usuários administradores (59492 e 59817) no banco map."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    script = __file__.replace("aplicar_usuario_admin.py", "aplicar_admins_proj_map.py")
    return subprocess.call([sys.executable, script])


if __name__ == "__main__":
    raise SystemExit(main())
