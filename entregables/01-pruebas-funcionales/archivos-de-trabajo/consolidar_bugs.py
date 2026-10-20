"""Numera los borradores de defectos (bugs/borrador_*.json) como BUG-001… en el orden de los casos.

    python consolidar_bugs.py

Los borradores los escribe quien ejecuta; aquí solo se numeran, se completa
el estado y la fecha (la de la ejecución del caso) y se aplican los ajustes de
severidad acordados en la revisión, cada uno con su motivo.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent

# Ajustes de la revisión: (borrador, campo, valor, motivo)
AJUSTES = {
    "borrador_TC-022.json": ("severidad", "Alta",
                             "Revisión: la carga manual falla pero la importación por CSV guarda los resultados "
                             "(hay alternativa), por eso Alta y no Crítica."),
}


def orden(p: Path):
    nombre = p.stem.replace("borrador_", "")
    tc, _, sufijo = nombre.partition("_")
    return tc, sufijo


def main():
    for viejo in (AQUI / "bugs").glob("BUG-*.json"):
        viejo.unlink()
    borradores = sorted((AQUI / "bugs").glob("borrador_*.json"), key=orden)
    for n, p in enumerate(borradores, start=1):
        b = json.loads(p.read_text(encoding="utf-8"))
        b["id"] = f"BUG-{n:03d}"
        b["estado"] = "Abierto"
        b["reportado_por"] = ""
        e = json.loads((AQUI / "ejecucion" / f"{b['tc']}.json").read_text(encoding="utf-8"))
        b["fecha"] = (e.get("fecha_hora") or "")[:10]
        if p.name in AJUSTES:
            campo, valor, motivo = AJUSTES[p.name]
            b[campo] = valor
            b["notas"] = (b.get("notas") or "").rstrip() + ("\n" if b.get("notas") else "") + motivo
        b["borrador"] = p.name
        (AQUI / "bugs" / f"{b['id']}.json").write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
        print(b["id"], b["tc"], b["severidad"], "/", b["prioridad"], "-", b["titulo"][:80])


if __name__ == "__main__":
    main()
