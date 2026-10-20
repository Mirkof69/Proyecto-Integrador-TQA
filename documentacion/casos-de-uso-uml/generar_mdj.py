"""Genera el proyecto de StarUML (Casos_de_Uso_FetalMedical.mdj) con el mismo modelo y la misma disposición.

    python generar_mdj.py

Un solo modelo UML: cada actor, caso de uso y relación existe UNA vez y cada
diagrama tiene sus vistas (como se hace en StarUML). Incluye puntos de
extensión, condición de cada «extend», estereotipo «system», actores
abstractos y la documentación de cada caso de uso (pestaña Documentation).

Para comprobar que StarUML lo abre y lo dibuja:
    StarUML.exe image Casos_de_Uso_FetalMedical.mdj -f png -o "salida\\<%=element.name%>.png"
(sin licencia, StarUML marca las imágenes exportadas como UNREGISTERED; dentro
del programa el diagrama se ve normal).
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import dibujar  # noqa: E402
from especificaciones import ESPECIFICACIONES  # noqa: E402
from modelo import ACTORES, DIAGRAMAS, HERENCIA, PUNTOS_EXTENSION  # noqa: E402

SALIDA = AQUI / "Casos_de_Uso_FetalMedical.mdj"
_n = itertools.count(1)


def nid() -> str:
    return f"FMBUML{next(_n):06d}"


def ref(x: str) -> dict:
    return {"$ref": x}


ESPEC = {e["id"]: e for e in ESPECIFICACIONES}


def documentacion(cid: str) -> str:
    e = ESPEC.get(cid)
    if not e:
        return ""
    partes = [e["descripcion"], "", "Actores: " + e["actores"], "", "Precondiciones:"]
    partes += [f"- {x}" for x in e["pre"]]
    partes += ["", "Flujo principal:"] + [f"{i}. {x}" for i, x in enumerate(e["flujo"], 1)]
    partes += ["", "Flujos alternativos:"] + [f"- {x}" for x in e["alternos"]]
    partes += ["", "Postcondiciones:"] + [f"- {x}" for x in e["post"]]
    partes += ["", f"Requisitos: {e['requisitos']}", f"Casos de prueba: {e['pruebas']}",
               f"Defectos abiertos: {e['defectos']}"]
    return "\n".join(partes)


def main():
    P, M = nid(), nid()
    elementos: list[dict] = []

    # ── elementos del modelo (uno por actor / caso de uso) ───────────────
    actor_id = {aid: nid() for aid in ACTORES}
    actores_json = {}
    for aid, (nombre, tipo, estereotipo, abstracto) in ACTORES.items():
        a = {"_type": "UMLActor", "_id": actor_id[aid], "_parent": ref(M), "name": nombre, "ownedElements": [],
             "documentation": f"Actor {tipo}" + (" (abstracto)" if abstracto else "")}
        if abstracto:
            a["isAbstract"] = True
        if estereotipo:
            a["stereotype"] = estereotipo
        actores_json[aid] = a
        elementos.append(a)

    nombres_cu: dict[str, str] = {}
    for d in DIAGRAMAS:
        for cid, (nombre, *_r) in d.get("casos", {}).items():
            nombres_cu.setdefault(cid, nombre)
    cu_id = {cid: nid() for cid in nombres_cu}
    punto_id: dict[tuple[str, str], str] = {}
    casos_json = {}
    for cid, nombre in sorted(nombres_cu.items()):
        u = {"_type": "UMLUseCase", "_id": cu_id[cid], "_parent": ref(M), "name": f"{cid} {nombre}",
             "ownedElements": [], "documentation": documentacion(cid)}
        if cid in PUNTOS_EXTENSION:
            u["extensionPoints"] = []
            for punto, _ext, _cond in PUNTOS_EXTENSION[cid]:
                pid = nid()
                punto_id[(cid, punto)] = pid
                u["extensionPoints"].append({"_type": "UMLExtensionPoint", "_id": pid, "_parent": ref(cu_id[cid]),
                                             "name": punto})
        casos_json[cid] = u
        elementos.append(u)

    # ── relaciones (únicas en el modelo) ─────────────────────────────────
    asociacion: dict[tuple[str, str], str] = {}
    relacion: dict[tuple[str, str, str], str] = {}
    gen_actor: dict[tuple[str, str], str] = {}

    def asoc(aid, cid):
        clave = (aid, cid)
        if clave not in asociacion:
            x = nid()
            asociacion[clave] = x
            actores_json[aid]["ownedElements"].append({
                "_type": "UMLAssociation", "_id": x, "_parent": ref(actor_id[aid]),
                "end1": {"_type": "UMLAssociationEnd", "_id": nid(), "_parent": ref(x), "reference": ref(actor_id[aid])},
                "end2": {"_type": "UMLAssociationEnd", "_id": nid(), "_parent": ref(x), "reference": ref(cu_id[cid])}})
        return asociacion[clave]

    def rel(tipo, origen, destino):
        clave = (tipo, origen, destino)
        if clave not in relacion:
            x = nid()
            relacion[clave] = x
            tipo_uml = {"include": "UMLInclude", "extend": "UMLExtend", "gen": "UMLGeneralization"}[tipo]
            r = {"_type": tipo_uml, "_id": x, "_parent": ref(cu_id[origen]), "source": ref(cu_id[origen]),
                 "target": ref(cu_id[destino])}
            if tipo == "extend":
                for punto, ext, cond in PUNTOS_EXTENSION.get(destino, []):
                    if ext == origen:
                        r["condition"] = cond
                        r["extensionLocations"] = [ref(punto_id[(destino, punto)])]
            casos_json[origen]["ownedElements"].append(r)
        return relacion[clave]

    def gen_a(hijo, padre):
        clave = (hijo, padre)
        if clave not in gen_actor:
            x = nid()
            gen_actor[clave] = x
            actores_json[hijo]["ownedElements"].append({
                "_type": "UMLGeneralization", "_id": x, "_parent": ref(actor_id[hijo]),
                "source": ref(actor_id[hijo]), "target": ref(actor_id[padre])})
        return gen_actor[clave]

    for hijo, padre in HERENCIA:
        gen_a(hijo, padre)

    # ── diagramas con sus vistas ─────────────────────────────────────────
    diagramas_json = []
    for d in DIAGRAMAS:
        D = nid()
        vistas = []
        diag = {"_type": "UMLUseCaseDiagram", "_id": D, "_parent": ref(M), "name": d["titulo"],
                "defaultDiagram": d["id"] == "general", "ownedViews": vistas}
        diagramas_json.append(diag)
        vista_actor, vista_caso = {}, {}

        def nodo_actor(aid, x, y):
            v = nid()
            vista_actor[aid] = v
            centro[v] = (x, y)
            vistas.append({"_type": "UMLActorView", "_id": v, "_parent": ref(D), "model": ref(actor_id[aid]),
                           "left": round(x - 20), "top": round(y - 40), "width": 40, "height": 80,
                           "suppressAttributes": True, "suppressOperations": True})

        centro = {}  # id de vista → (x, y) de su centro

        def borde(tipo_vista, modelo, cola, cabeza, fin=None):
            (x1, y1), (x2, y2) = centro[cola], (fin or centro[cabeza])
            vistas.append({"_type": tipo_vista, "_id": nid(), "_parent": ref(D), "model": ref(modelo),
                           "tail": ref(cola), "head": ref(cabeza), "lineStyle": 1,
                           "points": f"{round(x1)}:{round(y1)};{round(x2)}:{round(y2)}"})

        if d.get("tipo") == "actores":
            for aid, (x, y) in d["posiciones"].items():
                nodo_actor(aid, x, y)
            for hijo, padre in HERENCIA:
                borde("UMLGeneralizationView", gen_a(hijo, padre), vista_actor[hijo], vista_actor[padre])
            continue

        casos, actores, limite_der, _ancho, _alto = dibujar.construir(d)
        # alturas como las dibuja StarUML (compartimiento de puntos de extensión visible si el caso los tiene)
        alto_vista = {}
        for cid, c in casos.items():
            n_puntos = len(PUNTOS_EXTENSION.get(cid, []))
            ancho = 2 * (dibujar.RX_CON_PUNTOS if n_puntos else dibujar.RX)
            # StarUML escribe el nombre dentro del rectángulo inscrito en la elipse (ancho / √2)
            lineas = dibujar.partir(f"{cid} {nombres_cu[cid]}", max(10, int((ancho / 1.414 - 12) / 7.2)))
            base = max(70, round(len(lineas) * 22 * 1.414 + 30))  # medido en lo que exporta StarUML
            alto_vista[cid] = base + (22 + 15 * n_puntos if n_puntos else 0)
        # bajar lo que haga falta para que en cada columna nada se encime
        orden = sorted(casos.values(), key=lambda c: (c.y, c.x))
        desplaz, fondo_col, y_nuevo = 0.0, {}, {}
        for c in orden:
            top = c.y + desplaz - alto_vista[c.id] / 2
            ultimo = fondo_col.get(round(c.x))
            if ultimo is not None and top < ultimo + 40:
                desplaz += ultimo + 40 - top
                top = ultimo + 40
            y_nuevo[c.id] = top + alto_vista[c.id] / 2
            fondo_col[round(c.x)] = top + alto_vista[c.id]
        x_lim = d["_x_limite"]
        fondo = max(fondo_col.values()) + 40
        S = nid()
        elementos.append({"_type": "UMLUseCaseSubject", "_id": S, "_parent": ref(M), "name": d["sistema"]})
        vistas.append({"_type": "UMLUseCaseSubjectView", "_id": nid(), "_parent": ref(D), "model": ref(S),
                       "left": x_lim, "top": 40, "width": round(limite_der - x_lim), "height": round(fondo - 40)})
        for cid, c in casos.items():
            v = nid()
            vista_caso[cid] = v
            centro[v] = (c.x, y_nuevo[cid])
            ancho = 2 * (dibujar.RX_CON_PUNTOS if PUNTOS_EXTENSION.get(cid) else dibujar.RX)
            vistas.append({"_type": "UMLUseCaseView", "_id": v, "_parent": ref(D), "model": ref(cu_id[cid]),
                           "left": round(c.x - ancho / 2), "top": round(y_nuevo[cid] - alto_vista[cid] / 2),
                           "width": ancho, "height": alto_vista[cid], "wordWrap": True,
                           "suppressAttributes": True, "suppressOperations": True})
        for a in actores:
            y = sum(y_nuevo[i] for i in a.casos) / len(a.casos) if a.casos else a.y + desplaz / 2
            # en StarUML el nombre del actor es más ancho: se aleja un poco más del límite del sistema
            nodo_actor(a.id, a.x - 50 if a.lado == "izq" else a.x + 40, y)
        # actores sin asociaciones (solo heredan): entre sus vecinos, ya con las nuevas alturas
        lado_x = {}
        for cid, c in casos.items():
            semi = dibujar.RX_CON_PUNTOS if PUNTOS_EXTENSION.get(cid) else dibujar.RX
            n = len(PUNTOS_EXTENSION.get(cid, []))
            comp = 22 + 15 * n if n else 0  # StarUML dibuja la elipse arriba y el compartimiento debajo
            top = y_nuevo[cid] - alto_vista[cid] / 2
            elipse_y = top + (alto_vista[cid] - comp) / 2
            lado_x[cid] = (c.x - semi, c.x + semi, elipse_y)
        for aid, ids in d["actores_izq"]:
            for cid in ids:
                izq, _der, ey = lado_x[cid]
                borde("UMLAssociationView", asoc(aid, cid), vista_actor[aid], vista_caso[cid], (izq, ey))
        for aid, ids in d["actores_der"]:
            for cid in ids:
                _izq, der, ey = lado_x[cid]
                borde("UMLAssociationView", asoc(aid, cid), vista_actor[aid], vista_caso[cid], (der, ey))
        for hijo, padre in d.get("generalizaciones", []):
            borde("UMLGeneralizationView", gen_a(hijo, padre), vista_actor[hijo], vista_actor[padre])
        for tipo, origen, destino in d.get("relaciones", []):
            tv = {"include": "UMLIncludeView", "extend": "UMLExtendView", "gen": "UMLGeneralizationView"}[tipo]
            borde(tv, rel(tipo, origen, destino), vista_caso[origen], vista_caso[destino])

    proyecto = {
        "_type": "Project", "_id": P, "name": "Fetal Medical Bolivia",
        "ownedElements": [{"_type": "UMLModel", "_id": M, "_parent": ref(P), "name": "Modelo de casos de uso",
                           "ownedElements": diagramas_json + elementos}],
    }
    SALIDA.write_text(json.dumps(proyecto, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Escrito {SALIDA.name}: {len(diagramas_json)} diagramas, {len(ACTORES)} actores, {len(cu_id)} casos de uso, "
          f"{len(asociacion)} asociaciones, {len(relacion)} include/extend/generalización, "
          f"{len(gen_actor)} generalizaciones de actores")


if __name__ == "__main__":
    main()
