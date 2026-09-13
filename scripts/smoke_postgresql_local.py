# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Smoke HTTP local: login → ocupação → vínculo → viagem → baixa → banco de horas.

Requer API em http://127.0.0.1:5000 com PostgreSQL + ERP_PROVIDER=mock.
Admin seed: matrícula 59817 / senha 123.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import urllib.error
import urllib.request

BASE = os.getenv("REDMAPA_SMOKE_BASE", "http://127.0.0.1:5000").rstrip("/")
TZ = ZoneInfo("America/Sao_Paulo")
MATRICULA = os.getenv("REDMAPA_SMOKE_USER", "59817")
SENHA = os.getenv("REDMAPA_SMOKE_PASS", "123")


class CookieJar:
    def __init__(self) -> None:
        self.cookies: dict[str, str] = {}

    def store(self, headers) -> None:
        raw = headers.get_all("Set-Cookie") if hasattr(headers, "get_all") else None
        values = raw or []
        if not values:
            single = headers.get("Set-Cookie")
            if single:
                values = [single]
        for v in values:
            part = v.split(";", 1)[0]
            if "=" in part:
                name, val = part.split("=", 1)
                self.cookies[name.strip()] = val.strip()

    def header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())


JAR = CookieJar()


def req(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if JAR.cookies:
        headers["Cookie"] = JAR.header()
    request = urllib.request.Request(
        f"{BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as resp:
            JAR.store(resp.headers)
            raw = resp.read().decode("utf-8") or "{}"
            return int(resp.status), json.loads(raw)
    except urllib.error.HTTPError as e:
        JAR.store(e.headers)
        raw = e.read().decode("utf-8") or "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return int(e.code), payload


def log(step: str, http: int, **extra) -> None:
    print(json.dumps({"step": step, "http": http, **extra}, ensure_ascii=False))


def main() -> int:
    os.environ.setdefault("REDMAPA_SGBD", "postgresql")
    os.environ.setdefault("REDMAPA_CONFIG", "map_PostGree")

    results: list[dict] = []

    code, body = req("GET", "/api/v1/health")
    log("health", code, ok=body.get("ok"), sgbd=body.get("sgbd"))
    results.append({"step": "health", "http": code, "ok": body.get("ok")})
    if code != 200 or not body.get("ok"):
        print("API/DB indisponível — abortando smoke.", file=sys.stderr)
        return 1

    code, body = req(
        "POST", "/api/v1/auth/login", {"matricula": MATRICULA, "senha": SENHA}
    )
    log("login", code)
    results.append({"step": "login", "http": code})
    if code != 200:
        return 1

    code, body = req("GET", "/api/v1/mapas/ocupacao")
    log("ocupacao", code, ok=code == 200)
    results.append({"step": "ocupacao", "http": code})
    if code != 200:
        return 1

    # IDs via DAL (mesmo banco da API)
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from BackEnd.dal_factory import create_dal

    dal = create_dal(config_arquivo="map_PostGree", sgbd="postgresql")
    emp = dal.read(
        "SELECT id_empresa FROM tb_empresa WHERE ativo IS TRUE ORDER BY id_empresa LIMIT 1"
    )
    tur = dal.read(
        "SELECT id_turno FROM tb_turno WHERE ativo IS TRUE ORDER BY id_turno LIMIT 1"
    )
    lin = dal.read(
        "SELECT id_linha FROM tb_linha WHERE ativo IS TRUE ORDER BY id_linha LIMIT 1"
    )
    veis = dal.read(
        "SELECT id_veiculo FROM tb_veiculo WHERE ativo IS TRUE ORDER BY id_veiculo"
    )
    mots = dal.read(
        "SELECT id_motorista FROM tb_motorista WHERE ativo IS TRUE ORDER BY id_motorista"
    )
    if any(x is None or x.empty for x in (emp, tur, lin, veis, mots)):
        print(
            "Seed incompleto. Rode: python scripts/setup_postgresql_local.py",
            file=sys.stderr,
        )
        return 1

    id_empresa = int(emp.iloc[0]["id_empresa"])
    id_turno = int(tur.iloc[0]["id_turno"])
    id_linha = int(lin.iloc[0]["id_linha"])
    id_veiculo = int(veis.iloc[0]["id_veiculo"])
    id_motorista = int(mots.iloc[0]["id_motorista"])

    hoje = date.today()
    data_s = hoje.isoformat()
    # horários com data (formato dos testes)
    ini_jor = f"{data_s} 05:00:00"
    fim_jor = f"{data_s} 14:00:00"
    agora = datetime.now(TZ).replace(tzinfo=None)
    # janela única por execução para evitar sobreposição entre smokes
    stamp = agora.strftime("%H%M%S")
    h0 = int(stamp[0:2]) % 10
    hor_ini = f"{data_s} {h0:02d}:10:00"
    hor_fim = f"{data_s} {h0 + 3:02d}:10:00"
    chegada_ponto = f"{data_s} {h0:02d}:15:00"
    v_saida = f"{data_s} {h0:02d}:30:00"
    v_chegada = f"{data_s} {h0:02d}:50:00"

    code, body = req(
        "POST",
        "/api/v1/mapas",
        {
            "id_turno": id_turno,
            "id_empresa": id_empresa,
            "data": data_s,
            "inicio_jornada_des": ini_jor,
            "fim_jornada_des": fim_jor,
        },
    )
    log("criar_mapa", code, codigo=body.get("codigo"))
    results.append({"step": "criar_mapa", "http": code})
    if code not in (200, 201):
        print(body, file=sys.stderr)
        return 1
    id_mapa = int(body["mapa"]["id_registro"])

    # Liberar ocupação residual do lab (baixa scales EM_ANDAMENTO do veículo/motorista)
    occ = dal.read(
        """
        SELECT id_item FROM tb_item_map
        WHERE status_escala = 'EM_ANDAMENTO'
          AND (id_veiculo = ? OR id_motorista = ?)
        """,
        (id_veiculo, id_motorista),
    )
    if occ is not None and not occ.empty:
        for _, row in occ.iterrows():
            req(
                "POST",
                f"/api/v1/mapas/itens/{int(row['id_item'])}/baixa",
                {"motivo_baixa": "FIM_JORNADA", "observacao_baixa": "smoke cleanup"},
            )

    code, body = req(
        "POST",
        f"/api/v1/mapas/{id_mapa}/itens",
        {
            "id_linha": id_linha,
            "id_veiculo": id_veiculo,
            "id_motorista": id_motorista,
            "hor_ini_jor": hor_ini,
            "hor_fim_jor": hor_fim,
            "chegada_ponto": chegada_ponto,
        },
    )
    log("vincular", code, codigo=body.get("codigo"))
    results.append({"step": "vincular", "http": code})
    if code not in (200, 201) and len(veis) > 1 and len(mots) > 1:
        id_veiculo = int(veis.iloc[1]["id_veiculo"])
        id_motorista = int(mots.iloc[1]["id_motorista"])
        code, body = req(
            "POST",
            f"/api/v1/mapas/{id_mapa}/itens",
            {
                "id_linha": id_linha,
                "id_veiculo": id_veiculo,
                "id_motorista": id_motorista,
                "hor_ini_jor": hor_ini,
                "hor_fim_jor": hor_fim,
                "chegada_ponto": chegada_ponto,
            },
        )
        log("vincular_retry", code, codigo=body.get("codigo"))
        results.append({"step": "vincular_retry", "http": code})
    if code not in (200, 201):
        print(body, file=sys.stderr)
        return 1
    id_item = int(body["item"]["id_item"])

    code, body = req(
        "POST",
        f"/api/v1/mapas/itens/{id_item}/viagens",
        {
            "id_mapa_item": id_item,
            "horario_saida": v_saida,
            "horario_chegada": v_chegada,
            "qtd_pas_ida": 10,
            "qtd_pas_volta": 8,
        },
    )
    log("viagem", code, codigo=body.get("codigo"))
    results.append({"step": "viagem", "http": code})
    if code not in (200, 201):
        print(body, file=sys.stderr)
        return 1

    fim_real = f"{data_s} {h0 + 2:02d}:00:00"
    code, body = req(
        "POST",
        f"/api/v1/mapas/itens/{id_item}/baixa",
        {
            "fim_real": fim_real,
            "motivo_baixa": "FIM_JORNADA",
            "observacao_baixa": "smoke postgresql",
        },
    )
    status = (body.get("item") or {}).get("status_escala") or body.get("status_escala")
    log("baixa", code, status=status, codigo=body.get("codigo"))
    results.append({"step": "baixa", "http": code, "status": status})
    if code != 200:
        print(body, file=sys.stderr)
        return 1

    code, body = req(
        "GET",
        f"/api/v1/motoristas/{id_motorista}/banco-horas?data={data_s}",
    )
    log("banco_horas", code, ok=code == 200)
    results.append({"step": "banco_horas", "http": code})
    if code != 200:
        print(body, file=sys.stderr)
        return 1

    out = Path(root) / "backups" / "fase0" / "smoke_postgresql_local.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Smoke OK — evidência: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
