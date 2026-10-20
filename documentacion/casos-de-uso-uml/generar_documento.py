"""Documento «Casos de uso (UML)» de Fetal Medical Bolivia.

    python dibujar.py && node a_png.js && python generar_documento.py

Diagramas: diagramas/*.png (dibujados y comprobados por dibujar.py).
Especificaciones: especificaciones.py. Salida: Casos_de_Uso_UML.docx (y el PDF
con ..\\a_pdf.ps1).
"""
from __future__ import annotations

import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from especificaciones import ACTORES, ESPECIFICACIONES  # noqa: E402
from modelo import DIAGRAMAS, PUNTOS_EXTENSION  # noqa: E402

SALIDA = AQUI / "Casos_de_Uso_UML.docx"
AZUL = RGBColor(0x1F, 0x3A, 0x5F)
GRIS = RGBColor(0x22, 0x22, 0x22)
CAB = "4472C4"
ETQ = "D9E2F3"
ANCHO_UTIL = 17.0  # cm (A4 con márgenes de 2 cm)

NOMBRE_CU = {}
for d in DIAGRAMAS:
    for cid, (nombre, *_r) in d.get("casos", {}).items():
        NOMBRE_CU.setdefault(cid, nombre)


def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def poner(celda, texto, negrita=False, blanco=False, tam=9.5):
    celda.paragraphs[0].text = ""
    lineas = texto if isinstance(texto, list) else [texto]
    p = celda.paragraphs[0]
    for i, linea in enumerate(lineas):
        if i:
            p = celda.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(linea)
        r.font.name = "Arial"
        r.font.size = Pt(tam)
        r.font.bold = negrita
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if blanco else GRIS


def anchos(tabla, cms):
    tabla.autofit = False
    for col, w in zip(tabla.columns, cms):
        col.width = Cm(w)
    for fila in tabla.rows:
        celdas = fila._tr.tc_lst
        for i, tc in enumerate(celdas):
            span = tc.tcPr.find(qn("w:gridSpan")) if tc.tcPr is not None else None
            n = int(span.get(qn("w:val"))) if span is not None else 1
            tc.get_or_add_tcPr()
            from docx.table import _Cell
            _Cell(tc, tabla).width = Cm(sum(cms[i:i + n]))


def h(doc, texto, nivel=1):
    p = doc.add_heading(texto, level=nivel)
    for r in p.runs:
        r.font.color.rgb = AZUL
        r.font.name = "Arial"
    return p


def par(doc, texto, negrita=False, cursiva=False, tam=11, alinear=None, color=None):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.font.name = "Arial"
    r.font.size = Pt(tam)
    r.font.bold = negrita
    r.font.italic = cursiva
    if color:
        r.font.color.rgb = color
    if alinear is not None:
        p.alignment = alinear
    p.paragraph_format.space_after = Pt(6)
    return p


def vineta(doc, texto):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(texto)
    r.font.name = "Arial"
    r.font.size = Pt(11)


def imagen(doc, archivo, pie, alto_max=22.0):
    ruta = AQUI / "diagramas" / archivo
    w, hgt = Image.open(ruta).size
    ancho = min(ANCHO_UTIL, alto_max * w / hgt)
    doc.add_picture(str(ruta), width=Cm(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    par(doc, pie, cursiva=True, tam=9, alinear=WD_ALIGN_PARAGRAPH.CENTER)


def tabla(doc, encabezados, filas, cms, tam=9):
    t = doc.add_table(rows=1 + len(filas), cols=len(encabezados))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, e in enumerate(encabezados):
        poner(t.rows[0].cells[i], e, negrita=True, blanco=True, tam=tam)
        sombrear(t.rows[0].cells[i], CAB)
    for k, f in enumerate(filas, start=1):
        for i, v in enumerate(f):
            poner(t.rows[k].cells[i], v, tam=tam)
    anchos(t, cms)
    doc.add_paragraph()


def especificacion(doc, e):
    filas = [
        ("Caso de uso", f'{e["id"]} · {e["nombre"]}'),
        ("Actores", e["actores"]),
        ("Descripción", e["descripcion"]),
        ("Precondiciones", e["pre"]),
        ("Flujo principal", [f"{i}. {x}" for i, x in enumerate(e["flujo"], start=1)]),
        ("Flujos alternativos", e["alternos"]),
        ("Postcondiciones", e["post"]),
        ("Relaciones", e["relaciones"]),
        ("Requisitos", e["requisitos"]),
        ("Casos de prueba", e["pruebas"]),
        ("Defectos abiertos", e["defectos"]),
    ]
    t = doc.add_table(rows=len(filas), cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, (etq, valor) in enumerate(filas):
        poner(t.rows[k].cells[0], etq, negrita=True, blanco=(k == 0))
        sombrear(t.rows[k].cells[0], CAB if k == 0 else ETQ)
        poner(t.rows[k].cells[1], valor, negrita=(k == 0), blanco=(k == 0))
        if k == 0:
            sombrear(t.rows[k].cells[1], CAB)
    # la especificación no se parte entre páginas: cada fila «se mantiene con la siguiente» y no se corta
    for k, fila in enumerate(t.rows):
        trPr = fila._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if k < len(t.rows) - 1:
            for celda in fila.cells:
                for p in celda.paragraphs:
                    p.paragraph_format.keep_with_next = True
    anchos(t, [3.6, 13.4])
    doc.add_paragraph()


def relaciones_del_diagrama(d):
    filas = []
    for tipo, origen, destino in d.get("relaciones", []):
        if tipo == "include":
            filas.append([f"{destino} {NOMBRE_CU[destino]}", "«include»", f"{origen} {NOMBRE_CU[origen]}",
                          "Siempre: el caso base no se completa sin él."])
        elif tipo == "extend":
            punto, cond = next(((pt, c) for pt, ext, c in PUNTOS_EXTENSION.get(destino, []) if ext == origen),
                               ("—", "ver flujos alternativos del caso base"))
            filas.append([f"{origen} {NOMBRE_CU[origen]}", "«extend»", f"{destino} {NOMBRE_CU[destino]}",
                          f"Punto de extensión «{punto}». Condición: {cond}."])
        else:
            filas.append([f"{origen} {NOMBRE_CU[origen]}", "generalización", f"{destino} {NOMBRE_CU[destino]}",
                          "Es un tipo particular del caso padre: hereda su flujo y lo especializa."])
    return filas


def main():
    doc = docx.Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    for lado in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(s, lado, Cm(2.0))
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(11)

    # Portada
    for _ in range(4):
        doc.add_paragraph()
    par(doc, "UNIVERSIDAD PRIVADA FRANZ TAMAYO (UNIFRANZ)", negrita=True, tam=14, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "Testing y Aseguramiento de la Calidad (TQA) · Proyecto Integrador", tam=12,
        alinear=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()
    par(doc, "CASOS DE USO (UML)", negrita=True, tam=20, alinear=WD_ALIGN_PARAGRAPH.CENTER, color=AZUL)
    par(doc, "Fetal Medical Bolivia — historia clínica perinatal con apoyo de inteligencia artificial", tam=12,
        alinear=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()
    n_casos = len(NOMBRE_CU)
    par(doc, f"{len(DIAGRAMAS)} diagramas · {n_casos} casos de uso · {len(ESPECIFICACIONES)} especificaciones · "
             f"{len(ACTORES)} actores", tam=11, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(5):
        doc.add_paragraph()
    par(doc, "Integrantes: [Nombres del equipo]", alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "Docente: [Nombre del docente]", alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "La Paz, Bolivia · octubre de 2026", alinear=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # 1. Introducción
    h(doc, "1. Introducción")
    par(doc, "Este documento modela con diagramas de casos de uso UML lo que hace Fetal Medical Bolivia y quién lo "
             "hace. Complementa el Entregable 1 de pruebas funcionales: cada caso de uso indica los requisitos que "
             "cubre, los casos de prueba que lo verificaron y los defectos que quedaron abiertos.")
    h(doc, "1.1 Cómo leer los diagramas", 2)
    imagen(doc, "leyenda.png", "Figura 1 — Notación UML 2.5 utilizada (la misma de StarUML).", alto_max=5)
    for x in [
        "Actor primario (figura de palitos, a la IZQUIERDA del sistema): persona que inicia el caso de uso para "
        "lograr un objetivo (Recepción, Enfermería, Laboratorista, Médico, Administrador).",
        "Actor secundario (a la DERECHA del sistema): sistema externo al que el sistema le pide algo para cumplir el "
        "caso de uso. Lleva el estereotipo «system» sobre su nombre (Servicio de IA).",
        "Actor abstracto (nombre en cursiva): nadie lo es directamente; existe para que otros hereden de él "
        "(«Usuario del sistema», «Personal de salud»).",
        "Caso de uso (elipse): un objetivo completo del actor, con su identificador (CU-nn) y su nombre en verbo "
        "infinitivo. Si es base de un «extend», muestra el compartimiento «extension points» con sus puntos de "
        "extensión.",
        "Límite del sistema (rectángulo): lo que está dentro es responsabilidad de Fetal Medical Bolivia; los actores "
        "siempre quedan fuera.",
        "Asociación (línea continua, sin flecha): el actor participa en ese caso de uso.",
        "«include» (línea discontinua con punta abierta, del caso base al incluido): el caso base SIEMPRE ejecuta "
        "al incluido; se usa para comportamiento obligatorio y reutilizable.",
        "«extend» (línea discontinua con punta abierta, del extensor al caso base): comportamiento opcional que se "
        "inserta en un PUNTO DE EXTENSIÓN del caso base solo si se cumple su CONDICIÓN. El caso base funciona "
        "completo sin él.",
        "Generalización (línea continua con triángulo hueco hacia el padre): el hijo hereda todo lo del padre. "
        "Entre actores, refleja los permisos reales del sistema; entre casos de uso, especializa (las calculadoras).",
    ]:
        vineta(doc, x)
    h(doc, "1.2 Criterios de dibujo", 2)
    par(doc, "Los diagramas salen de un único modelo (casos_de_uso/modelo.py) con una comprobación automática que "
             "se niega a dibujar si dos líneas se cruzan, si una línea pasa sobre un caso de uso o un actor que no "
             "une, si un estereotipo tapa una elipse, si dos elipses se tocan, si un actor primario no está a la "
             f"izquierda o uno secundario no está a la derecha, o si un caso de uso cambia de nombre entre "
             f"diagramas. Los {len(DIAGRAMAS)} diagramas la superan. Las asociaciones llegan al extremo lateral de "
             "cada elipse y los actores de un mismo lado se ordenan según los casos que usan, para que ninguna línea "
             "se atraviese con otra.")
    h(doc, "1.3 Proyecto de StarUML", 2)
    par(doc, "El mismo modelo está en casos_de_uso/Casos_de_Uso_FetalMedical.mdj, que se abre con StarUML "
             "(Archivo → Abrir). Cada actor, caso de uso y relación existe una sola vez en el modelo y cada diagrama "
             "tiene sus vistas, como se trabaja en StarUML: al renombrar un caso de uso cambia en todos los "
             "diagramas. Incluye los puntos de extensión, la condición de cada «extend» (propiedad Condition), el "
             "estereotipo «system», los actores abstractos (isAbstract) y la especificación de cada caso de uso en "
             "su pestaña Documentation.")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # 2. Actores
    h(doc, "2. Actores")
    tabla(doc, ["Actor", "Tipo", "Qué hace", "Herencia"], [list(a) for a in ACTORES], [3.4, 2.6, 7.6, 3.4])
    par(doc, "Los permisos de cada actor salen de la tabla única de permisos del sistema "
             "(Backend/usuarios/permisos_por_rol.py). Un cargo (obstetriz, nutricionista…) es un actor que se basa en "
             "un rol y solo puede usar una parte de sus casos de uso (CU-22).", tam=10)

    # 3. Diagramas
    numero = 3
    figura = 2
    for d in DIAGRAMAS:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        h(doc, f"{numero}. {d['titulo']}")
        par(doc, d["descripcion"])
        imagen(doc, f"{d['id']}.png", f"Figura {figura} — {d['titulo']}.")
        figura += 1
        rel = relaciones_del_diagrama(d)
        if rel:
            h(doc, f"{numero}.1 Relaciones entre casos de uso", 2)
            tabla(doc, ["Caso de uso", "Relación", "Con", "Cuándo"], rel, [4.6, 2.4, 4.6, 5.4], tam=8.5)
        specs = [e for e in ESPECIFICACIONES if e["diagrama"] == d["id"]]
        if specs:
            h(doc, f"{numero}.{2 if rel else 1} Especificación de los casos de uso", 2)
            for e in specs:
                especificacion(doc, e)
        numero += 1

    # Trazabilidad
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h(doc, f"{numero}. Matriz de trazabilidad")
    par(doc, "Caso de uso → requisito → casos de prueba del Entregable 1 → defectos abiertos.")
    tabla(doc, ["Caso de uso", "Requisitos", "Casos de prueba", "Defectos"],
          [[f'{e["id"]} {e["nombre"]}', e["requisitos"], e["pruebas"], e["defectos"]] for e in ESPECIFICACIONES],
          [6.4, 3.2, 4.2, 3.2], tam=8.5)

    doc.save(str(SALIDA))
    print(f"Escrito {SALIDA.name}: {len(DIAGRAMAS)} diagramas, {n_casos} casos, {len(ESPECIFICACIONES)} especificaciones")


if __name__ == "__main__":
    main()
