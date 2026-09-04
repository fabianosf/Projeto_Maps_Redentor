# PROJ_ONIX — fábrica DAL (banco crip)
from __future__ import annotations
import os
from typing import Optional
from DAL.DAL import DAL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS_CRIP_DIR = os.path.join(BASE_DIR, "DAL", "arquivos_crip")
_dal_singleton: Optional[DAL] = None


def normalizar_config_arquivo(valor: str) -> str:
    nome = (valor or "crip").strip()
    if nome.lower().endswith(".dat"):
        nome = nome[:-4]
    return nome


def create_dal(
    config_arquivo: Optional[str] = None,
    sgbd: Optional[str] = None,
    pasta_conf: Optional[str] = None,
) -> DAL:
    cfg = normalizar_config_arquivo(
        config_arquivo or os.getenv("PROJ_ONIX_CONFIG", "crip")
    )
    sgbd_norm = (sgbd or os.getenv("PROJ_ONIX_SGBD", "mariadb")).strip().lower()
    pasta = pasta_conf or ARQUIVOS_CRIP_DIR
    return DAL(config_arquivo=cfg, pasta_conf=pasta, sgbd=sgbd_norm)


def get_dal_instance() -> DAL:
    global _dal_singleton
    if _dal_singleton is None:
        _dal_singleton = create_dal()
    return _dal_singleton
