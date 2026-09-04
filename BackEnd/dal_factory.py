# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Fábrica única de instâncias DAL para BackEnd e scripts de manutenção."""

from __future__ import annotations

import os
from typing import Optional

from .DAL import DAL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVOS_CRIP_DIR = os.path.join(BASE_DIR, "DAL", "arquivos_crip")

_dal_singleton: Optional[DAL] = None
_erp_dal_singleton: Optional[DAL] = None


def normalizar_config_arquivo(valor: str) -> str:
    nome = (valor or "map").strip()
    if nome.lower().endswith(".dat"):
        nome = nome[:-4]
    return nome


def create_dal(
    config_arquivo: Optional[str] = None,
    sgbd: Optional[str] = None,
    pasta_conf: Optional[str] = None,
) -> DAL:
    """Cria DAL usando config criptografada (padrão: map.dat / MariaDB)."""
    cfg = normalizar_config_arquivo(
        config_arquivo or os.getenv("REDMAPA_CONFIG", "map")
    )
    sgbd_norm = (sgbd or os.getenv("REDMAPA_SGBD", "mariadb")).strip().lower()
    pasta = pasta_conf or ARQUIVOS_CRIP_DIR
    return DAL(config_arquivo=cfg, pasta_conf=pasta, sgbd=sgbd_norm)


def get_dal_instance() -> DAL:
    """Instância singleton usada pela aplicação Flask."""
    global _dal_singleton
    if _dal_singleton is None:
        _dal_singleton = create_dal()
    return _dal_singleton


def get_erp_dal_instance() -> DAL:
    """Instância singleton DAL Oracle (erp.dat) para consultas ao ERP."""
    global _erp_dal_singleton
    if _erp_dal_singleton is None:
        cfg = normalizar_config_arquivo(os.getenv("REDMAPA_ERP_CONFIG", "erp"))
        sgbd = (os.getenv("REDMAPA_ERP_SGBD", "oracle")).strip().lower()
        _erp_dal_singleton = create_dal(config_arquivo=cfg, sgbd=sgbd)
    return _erp_dal_singleton
