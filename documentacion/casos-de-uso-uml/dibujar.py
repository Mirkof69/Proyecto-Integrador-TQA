"""Dibuja los diagramas de casos de uso (UML 2.5) en SVG y comprueba que se lean bien.

    python dibujar.py          → diagramas/*.svg y el informe de comprobación

Notación (la misma que usa StarUML):
  · actor: figura de palitos con su nombre debajo; abstracto en cursiva; con
    estereotipo («system») sobre el nombre. Primarios a la izquierda del
    sistema, secundarios a la derecha.
  · caso de uso: elipse con su identificador y nombre; si es base de un
    «extend», muestra el compartimiento «extension points» con sus puntos.
  · límite del sistema: rectángulo con el nombre del sistema arriba.
  · asociación: línea continua actor–caso de uso.
  · «include» y «extend»: línea discontinua con punta abierta y su estereotipo.
  · generalización: línea continua con triángulo hueco hacia el padre.

Comprobaciones (si alguna falla, el diagrama no se escribe):
  · ninguna línea cruza a otra;
  · ninguna línea pasa sobre un caso de uso o un actor que no une;
  · ningún estereotipo tapa un caso de uso; las elipses no se tocan;
  · los actores primarios están a la izquierda y los secundarios a la derecha;
  · un mismo caso de uso se llama igual en todos los diagramas.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from modelo import ACTORES, DIAGRAMAS, HERENCIA, PUNTOS_EXTENSION  # noqa: E402

SALIDA = AQUI / "diagramas"
FUENTE = "Arial, Helvetica, sans-serif"
TINTA = "#1d2a36"
BORDE_SISTEMA = "#3d5266"
FONDO_SISTEMA = "#f7f9fb"

X_ACTOR_IZQ = 80
X_LIMITE = 190
SEP_COLUMNAS = 320
RX = 112
RX_CON_PUNTOS = 124
MARGEN_SUP = 70
CASOS_ACTUALES: list = []


# ─── geometría ───────────────────────────────────────────────────────────────
def partir(texto: str, ancho=24) -> list[str]:
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + (1 if actual else 0) <= ancho:
            actual = f"{actual} {p}".strip()
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


class Caso:
    def __init__(self, cid, nombre, x, y, puntos=()):
        self.id, self.nombre, self.x, self.y = cid, nombre, x, y
        self.lineas = partir(nombre)
        self.puntos = list(puntos)
        self.rx = RX_CON_PUNTOS if self.puntos else RX
        filas = 1 + len(self.lineas) + (1 + len(self.puntos) if self.puntos else 0)
        self.ry = 9 + 8 * filas + (6 if self.puntos else 0)

    def dentro(self, px, py, holgura=1.0):
        return ((px - self.x) / (self.rx * holgura)) ** 2 + ((py - self.y) / (self.ry * holgura)) ** 2 < 1

    def borde(self, hacia_x, hacia_y):
        dx, dy = hacia_x - self.x, hacia_y - self.y
        if dx == 0 and dy == 0:
            return self.x, self.y
        t = 1 / math.sqrt((dx / self.rx) ** 2 + (dy / self.ry) ** 2)
        return self.x + dx * t, self.y + dy * t


class Actor:
    def __init__(self, aid, lado, casos):
        self.id, self.lado, self.casos = aid, lado, casos
        self.nombre, self.tipo, self.estereotipo, self.abstracto = ACTORES[aid]
        self.x = self.y = 0.0

    @property
    def lineas_nombre(self):
        return partir(self.nombre, 14)

    @property
    def caja(self):
        abajo = 50 + 14 * (len(self.lineas_nombre) + (1 if self.estereotipo else 0))
        return (self.x - 46, self.y - 40, self.x + 46, self.y + abajo)

    def ancla(self):
        return (self.x + 18 if self.lado == "izq" else self.x - 18), self.y - 8

    def pie(self):
        return self.x, self.caja[3] + 6

    def cabeza(self):
        return self.x, self.y - 42


def segmentos_cruzan(a, b, c, d) -> bool:
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return o1 != o2 and o3 != o4 and 0 not in (o1, o2, o3, o4)


def comparte_extremo(s1, s2, tol=0.5) -> bool:
    return any(math.dist(p, q) < tol for p in s1[:2] for q in s2[:2])


# ─── construcción ────────────────────────────────────────────────────────────
def puntos_en_diagrama(d: dict, cid: str) -> list[str]:
    """Puntos de extensión del caso base cuyos extensores aparecen en este diagrama."""
    if d.get("puntos") is False:
        return []
    extensores = {o for t, o, _ in d.get("relaciones", []) if t == "extend"}
    return [p for p, ext, _ in PUNTOS_EXTENSION.get(cid, []) if ext in extensores]


def construir(d: dict):
    alto_fila = d.get("alto_fila", 92)
    x_limite = d.get("x_limite", X_LIMITE)
    casos = {}
    for cid, (nombre, col, fila) in d["casos"].items():
        x = x_limite + 40 + RX_CON_PUNTOS + col * SEP_COLUMNAS
        y = MARGEN_SUP + 56 + fila * alto_fila
        casos[cid] = Caso(cid, nombre, x, y, puntos_en_diagrama(d, cid))
    limite_der = max(c.x + c.rx for c in casos.values()) + 40
    alto = max(c.y + c.ry for c in casos.values()) + 40

    actores = []
    for lado, lista in (("izq", d["actores_izq"]), ("der", d["actores_der"])):
        previos = []
        for aid, ids in lista:
            a = Actor(aid, lado, ids)
            a.x = X_ACTOR_IZQ if lado == "izq" else limite_der + d.get("dist_der", 130)
            if ids:
                a.y = sum(casos[i].y for i in ids) / len(ids)
            previos.append(a)
        for i, a in enumerate(previos):
            if not a.casos:
                arriba = previos[i - 1].y if i > 0 else MARGEN_SUP + 60
                abajo = next((b.y for b in previos[i + 1:] if b.casos), arriba + 300)
                a.y = (arriba + abajo) / 2 if abajo > arriba else arriba + 160
        for i in range(1, len(previos)):
            minimo = previos[i - 1].caja[3] - previos[i - 1].y + 110
            if previos[i].y < previos[i - 1].y + minimo:
                previos[i].y = previos[i - 1].y + minimo
        actores += previos
    if actores:
        alto = max(alto, max(a.caja[3] + 20 for a in actores))
    ancho = (limite_der + d.get("dist_der", 130) + 100) if d["actores_der"] else limite_der + 30
    d["_x_limite"] = x_limite
    return casos, actores, limite_der, ancho, alto + 20


def lineas_del_diagrama(d, casos, actores):
    por_id = {a.id: a for a in actores}
    lineas = []
    for a in actores:
        ax, ay = a.ancla()
        for cid in a.casos:
            c = casos[cid]
            fin = (c.x - c.rx, c.y) if a.lado == "izq" else (c.x + c.rx, c.y)
            lineas.append(((ax, ay), fin, "asociacion", a.id, cid))
    for hijo, padre in d.get("generalizaciones", []):
        h, p = por_id[hijo], por_id[padre]
        if h.y > p.y:
            lineas.append((h.cabeza(), p.pie(), "gen_actor", hijo, padre))
        else:
            lineas.append((h.pie(), p.cabeza(), "gen_actor", hijo, padre))
    for tipo, origen, destino in d.get("relaciones", []):
        o, t = casos[origen], casos[destino]
        lineas.append((o.borde(t.x, t.y), t.borde(o.x, o.y), tipo, origen, destino))
    return lineas


def etiqueta_pos(p1, p2, texto):
    # «include» sale del caso base (p1) y «extend» llega a él (p2): el rótulo va más cerca del otro extremo,
    # donde las líneas que comparten caso base ya están separadas y se ve a cuál pertenece
    t = 0.4 if "extend" in texto else 0.6
    if math.dist(p1, p2) < 150:  # líneas cortas: al medio, donde hay más espacio
        t = 0.5
    mx, my = p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t
    ancho = 7.0 * len(texto)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy) or 1
    ox, oy = -dy / n * 10, dx / n * 10
    if oy > 0:
        ox, oy = -ox, -oy
    candidatos = [(mx + ox, my + oy - 2), (mx - ox, my - oy + 12)]

    def tapa(ex, ey):
        return any(c.dentro(ex + ddx, ey + ddy, 1.02) for c in CASOS_ACTUALES
                   for ddx in (-ancho / 2, 0, ancho / 2) for ddy in (-9, 0, 3))
    ex, ey = next((c for c in candidatos if not tapa(*c)), candidatos[0])
    return ex, ey, ancho


def comprobar(d, casos, actores, lineas) -> list[str]:
    problemas = []
    for a in actores:
        if a.tipo == "secundario" and a.lado != "der":
            problemas.append(f"el actor secundario {a.id} debe ir a la derecha")
        if a.tipo == "primario" and a.lado != "izq":
            problemas.append(f"el actor primario {a.id} debe ir a la izquierda")
    lista = list(casos.values())
    for i, a in enumerate(lista):
        for b in lista[i + 1:]:
            if abs(a.x - b.x) < a.rx + b.rx + 8 and abs(a.y - b.y) < a.ry + b.ry + 8:
                problemas.append(f"elipses demasiado juntas: {a.id} y {b.id}")
    for i, s1 in enumerate(lineas):
        for s2 in lineas[i + 1:]:
            if not comparte_extremo(s1, s2) and segmentos_cruzan(s1[0], s1[1], s2[0], s2[1]):
                problemas.append(f"se cruzan: {s1[3]}→{s1[4]} y {s2[3]}→{s2[4]}")
    for s in lineas:
        (x1, y1), (x2, y2) = s[0], s[1]
        for k in range(1, 200):
            t = k / 200
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            for c in lista:
                if c.id not in (s[3], s[4]) and c.dentro(px, py, 1.06):
                    problemas.append(f"la línea {s[3]}→{s[4]} pasa sobre {c.id}")
                    break
            for a in actores:
                if a.id in (s[3], s[4]):
                    continue
                x0, y0, x9, y9 = a.caja
                if x0 < px < x9 and y0 < py < y9:
                    problemas.append(f"la línea {s[3]}→{s[4]} pasa sobre el actor {a.id}")
                    break
        if s[2] in ("include", "extend"):
            ex, ey, ancho = etiqueta_pos(s[0], s[1], f"«{s[2]}»")
            for c in lista:
                if any(c.dentro(ex + dx, ey + dy, 1.02) for dx in (-ancho / 2, 0, ancho / 2) for dy in (-9, 0, 3)):
                    problemas.append(f"el estereotipo de {s[3]}→{s[4]} tapa {c.id}")
    return sorted(set(problemas))


# ─── SVG ─────────────────────────────────────────────────────────────────────
def svg_actor(a: Actor) -> str:
    x, y = a.x, a.y
    t = f'stroke="{TINTA}" stroke-width="1.8"'
    partes = [
        f'<circle cx="{x}" cy="{y - 30}" r="10" fill="#fff" {t}/>',
        f'<line x1="{x}" y1="{y - 20}" x2="{x}" y2="{y + 8}" {t}/>',
        f'<line x1="{x - 16}" y1="{y - 10}" x2="{x + 16}" y2="{y - 10}" {t}/>',
        f'<line x1="{x}" y1="{y + 8}" x2="{x - 12}" y2="{y + 28}" {t}/>',
        f'<line x1="{x}" y1="{y + 8}" x2="{x + 12}" y2="{y + 28}" {t}/>',
    ]
    fila = 0
    if a.estereotipo:
        partes.append(f'<text x="{x}" y="{y + 44}" text-anchor="middle" font-size="11.5" '
                      f'fill="{TINTA}">«{escape(a.estereotipo)}»</text>')
        fila = 1
    estilo = 'font-style="italic" ' if a.abstracto else ""
    for i, linea in enumerate(a.lineas_nombre):
        partes.append(f'<text x="{x}" y="{y + 44 + (fila + i) * 14}" text-anchor="middle" {estilo}'
                      f'font-weight="700" font-size="13" fill="{TINTA}">{escape(linea)}</text>')
    return "\n".join(partes)


def svg_caso(c: Caso) -> str:
    partes = [f'<ellipse cx="{c.x:.1f}" cy="{c.y:.1f}" rx="{c.rx}" ry="{c.ry}" fill="#ffffff" '
              f'stroke="{TINTA}" stroke-width="1.6"/>']
    filas = 1 + len(c.lineas) + (1 + len(c.puntos) if c.puntos else 0)
    y = c.y - (filas - 1) * 7.6 - (3 if c.puntos else 0)
    partes.append(f'<text x="{c.x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="10" fill="#5a6b7a" '
                  f'font-weight="700">{c.id}</text>')
    for linea in c.lineas:
        y += 15
        partes.append(f'<text x="{c.x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" '
                      f'fill="{TINTA}">{escape(linea)}</text>')
    if c.puntos:
        y += 11
        semi = c.rx * math.sqrt(max(0.0, 1 - ((y - c.y) / c.ry) ** 2))
        partes.append(f'<line x1="{c.x - semi:.1f}" y1="{y:.1f}" x2="{c.x + semi:.1f}" y2="{y:.1f}" '
                      f'stroke="{TINTA}" stroke-width="1.1"/>')
        y += 4
        partes.append(f'<text x="{c.x:.1f}" y="{y + 9:.1f}" text-anchor="middle" font-size="10" font-style="italic" '
                      f'fill="#5a6b7a">extension points</text>')
        for p in c.puntos:
            y += 13.5
            partes.append(f'<text x="{c.x:.1f}" y="{y + 9:.1f}" text-anchor="middle" font-size="11" '
                          f'fill="{TINTA}">{escape(p)}</text>')
    return "\n".join(partes)


def punta_abierta(p1, p2, largo=11, abre=0.45):
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    a1 = (p2[0] - largo * math.cos(ang - abre), p2[1] - largo * math.sin(ang - abre))
    a2 = (p2[0] - largo * math.cos(ang + abre), p2[1] - largo * math.sin(ang + abre))
    return (f'<polyline points="{a1[0]:.1f},{a1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" '
            f'fill="none" stroke="{TINTA}" stroke-width="1.5"/>')


def triangulo_hueco(p1, p2, largo=14, abre=0.5):
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    a1 = (p2[0] - largo * math.cos(ang - abre), p2[1] - largo * math.sin(ang - abre))
    a2 = (p2[0] - largo * math.cos(ang + abre), p2[1] - largo * math.sin(ang + abre))
    return (f'<polygon points="{a1[0]:.1f},{a1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" '
            f'fill="#fff" stroke="{TINTA}" stroke-width="1.5"/>')


def recortar(p1, p2, cuanto):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy) or 1
    return p2[0] - dx / n * cuanto, p2[1] - dy / n * cuanto


def svg_linea(s, fondo=FONDO_SISTEMA) -> str:
    p1, p2, tipo = s[0], s[1], s[2]
    if tipo == "asociacion":
        return (f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                f'stroke="{TINTA}" stroke-width="1.5"/>')
    if tipo in ("gen_actor", "gen"):
        fin = recortar(p1, p2, 13)
        return (f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{fin[0]:.1f}" y2="{fin[1]:.1f}" '
                f'stroke="{TINTA}" stroke-width="1.5"/>\n' + triangulo_hueco(p1, p2))
    texto = f"«{tipo}»"
    ex, ey, ancho = etiqueta_pos(p1, p2, texto)
    return "\n".join([
        f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="{TINTA}" '
        f'stroke-width="1.4" stroke-dasharray="7 5"/>',
        punta_abierta(p1, p2),
        f'<rect x="{ex - ancho / 2 - 2:.1f}" y="{ey - 11:.1f}" width="{ancho + 4:.1f}" height="14" '
        f'fill="{fondo}" opacity="0.94"/>',
        f'<text x="{ex:.1f}" y="{ey:.1f}" text-anchor="middle" font-size="11.5" fill="{TINTA}">{escape(texto)}</text>',
    ])


def svg_diagrama(d, casos, actores, limite_der, ancho, alto, lineas) -> str:
    top = MARGEN_SUP - 30
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho:.0f}" height="{alto:.0f}" '
        f'viewBox="0 0 {ancho:.0f} {alto:.0f}" font-family="{FUENTE}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<rect x="{d["_x_limite"]}" y="{top}" width="{limite_der - d["_x_limite"]:.0f}" '
        f'height="{alto - top - 14:.0f}" fill="{FONDO_SISTEMA}" stroke="{BORDE_SISTEMA}" stroke-width="1.6"/>',
        f'<text x="{(d["_x_limite"] + limite_der) / 2:.0f}" y="{top + 24}" text-anchor="middle" font-size="14.5" '
        f'font-weight="700" fill="{TINTA}">{escape(d["sistema"])}</text>',
    ]
    partes += [svg_linea(s) for s in lineas]
    partes += [svg_caso(c) for c in casos.values()]
    partes += [svg_actor(a) for a in actores]
    partes.append("</svg>")
    return "\n".join(partes)


def diagrama_actores(d) -> tuple[str, list[str]]:
    """Jerarquía de actores: solo actores y generalizaciones (sin límite del sistema)."""
    actores = {}
    for aid, (x, y) in d["posiciones"].items():
        a = Actor(aid, "izq", [])
        a.x, a.y = x, y
        actores[aid] = a
    lineas, arboles = [], []
    hijos_de: dict[str, list[str]] = {}
    for hijo, padre in HERENCIA:
        hijos_de.setdefault(padre, []).append(hijo)
    for padre, hijos in hijos_de.items():
        p = actores[padre]
        if len(hijos) > 1:
            # estilo árbol: un solo triángulo bajo el padre y una barra que reparte a cada hijo
            px, py = p.pie()
            y_barra = (py + min(actores[h].cabeza()[1] for h in hijos)) / 2
            arboles.append((p, [actores[h] for h in hijos], y_barra))
            lineas.append(((px, y_barra), (px, py), "gen_actor", "barra", padre))
            xs = [actores[h].x for h in hijos] + [px]
            lineas.append(((min(xs), y_barra), (max(xs), y_barra), "barra", "barra", "barra"))
            for h in hijos:
                hx, hy = actores[h].cabeza()
                lineas.append(((hx, hy), (hx, y_barra), "barra", h, "barra"))
        else:
            h = actores[hijos[0]]
            lineas.append((h.cabeza(), p.pie(), "gen_actor", hijos[0], padre))
    problemas = comprobar({}, {}, [], [x for x in lineas if x[2] != "barra"])
    for s in lineas:
        (x1, y1), (x2, y2) = s[0], s[1]
        for k in range(1, 200):
            px, py = x1 + (x2 - x1) * k / 200, y1 + (y2 - y1) * k / 200
            for a in actores.values():
                if a.id not in (s[3], s[4]):
                    x0, y0, x9, y9 = a.caja
                    if x0 < px < x9 and y0 < py < y9:
                        problemas.append(f"la generalización {s[3]}→{s[4]} pasa sobre {a.id}")
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{d["ancho"]}" height="{d["alto"]}" '
              f'viewBox="0 0 {d["ancho"]} {d["alto"]}" font-family="{FUENTE}">',
              '<rect width="100%" height="100%" fill="#ffffff"/>']
    for x in lineas:
        if x[2] == "barra":
            (x1, y1), (x2, y2) = x[0], x[1]
            partes.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="{TINTA}" stroke-width="1.5"/>')
        else:
            partes.append(svg_linea(x, "#ffffff"))
    partes += [svg_actor(a) for a in actores.values()]
    partes.append("</svg>")
    return "\n".join(partes), sorted(set(problemas))


def svg_leyenda() -> str:
    a = Actor("medico", "izq", [])
    a.x, a.y = 60, 62
    s = Actor("ia", "der", [])
    s.x, s.y = 200, 62
    c = Caso("CU-nn", "Caso de uso", 400, 70, ["punto de extensión"])
    s_inc = ((580, 40), (700, 40), "include", "", "")
    s_ext = ((580, 92), (700, 92), "extend", "", "")
    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="190" viewBox="0 0 1180 190" '
        f'font-family="{FUENTE}">', '<rect width="100%" height="100%" fill="#fff"/>',
        svg_actor(a), svg_actor(s), svg_caso(c),
        f'<text x="60" y="140" text-anchor="middle" font-size="10.5" fill="#5a6b7a">primario (izquierda)</text>',
        f'<text x="200" y="154" text-anchor="middle" font-size="10.5" fill="#5a6b7a">secundario (derecha)</text>',
        svg_linea(s_inc, "#fff"), svg_linea(s_ext, "#fff"),
        f'<text x="715" y="44" font-size="11" fill="{TINTA}">el caso base SIEMPRE ejecuta al incluido</text>',
        f'<text x="715" y="90" font-size="11" fill="{TINTA}">el extensor se agrega al caso base en su punto de</text>',
        f'<text x="715" y="104" font-size="11" fill="{TINTA}">extensión, solo si se cumple la condición</text>',
        f'<line x1="580" y1="140" x2="687" y2="140" stroke="{TINTA}" stroke-width="1.5"/>',
        triangulo_hueco((580, 140), (700, 140)),
        f'<text x="715" y="144" font-size="11" fill="{TINTA}">generalización: el hijo hereda del padre</text>',
        f'<line x1="300" y1="165" x2="345" y2="165" stroke="{TINTA}" stroke-width="1.5"/>',
        f'<text x="352" y="169" font-size="11" fill="{TINTA}">asociación</text>',
        f'<rect x="440" y="152" width="120" height="26" fill="{FONDO_SISTEMA}" stroke="{BORDE_SISTEMA}" stroke-width="1.6"/>',
        f'<text x="500" y="169" text-anchor="middle" font-size="11" fill="{TINTA}">límite del sistema</text>',
        '</svg>',
    ]
    return "\n".join(partes)


def main() -> int:
    SALIDA.mkdir(exist_ok=True)
    total = 0
    nombres: dict[str, str] = {}
    for d in DIAGRAMAS:
        for cid, (nombre, *_r) in d.get("casos", {}).items():
            if nombres.setdefault(cid, nombre) != nombre:
                print(f"✗ {cid} tiene dos nombres: «{nombres[cid]}» y «{nombre}»")
                total += 1
    for d in DIAGRAMAS:
        if d.get("tipo") == "actores":
            svg, problemas = diagrama_actores(d)
            n_lineas = len(HERENCIA)
            resumen = f"{len(d['posiciones'])} actores, {n_lineas} generalizaciones"
        else:
            casos, actores, limite_der, ancho, alto = construir(d)
            CASOS_ACTUALES[:] = list(casos.values())
            lineas = lineas_del_diagrama(d, casos, actores)
            problemas = comprobar(d, casos, actores, lineas)
            svg = svg_diagrama(d, casos, actores, limite_der, ancho, alto, lineas)
            resumen = f"{len(casos)} casos, {len(actores)} actores, {len(lineas)} líneas ({ancho:.0f}×{alto:.0f})"
        if problemas:
            total += len(problemas)
            print(f"✗ {d['id']}:")
            for p in problemas:
                print(f"     {p}")
            continue
        (SALIDA / f"{d['id']}.svg").write_text(svg, encoding="utf-8")
        print(f"✓ {d['id']}: {resumen}, sin cruces")
    (SALIDA / "leyenda.svg").write_text(svg_leyenda(), encoding="utf-8")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
