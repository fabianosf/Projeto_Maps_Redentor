import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}

odt = Path(__file__).resolve().parents[1] / "Doc" / "Doc_Proj_Map.odt"
root = ET.fromstring(zipfile.ZipFile(odt).read("content.xml"))
text = root.find(".//office:text", NS)

out = []
for ti, table in enumerate(text.findall(".//table:table", NS)):
    flat = " ".join("".join(table.itertext()).split())
    if any(k in flat for k in ["RF-UI", "Stack de apresent", "Prioridade", "Crit"]):
        out.append(f"TABLE {ti} ({len(table.findall('table:table-row', NS))} rows)")
        for row in table.findall("table:table-row", NS):
            cells = [
                " ".join("".join(c.itertext()).split())
                for c in row.findall("table:table-cell", NS)
            ]
            out.append(" | ".join(cells))
        out.append("---")

Path(__file__).resolve().parents[1].joinpath("Doc/_table_dump.txt").write_text(
    "\n".join(out), encoding="utf-8"
)
print("written", len(out), "lines")
