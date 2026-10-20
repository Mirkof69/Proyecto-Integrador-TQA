"""Genera el documento del Entregable 1 (Pruebas Funcionales) y sus anexos.

    python generar_documento.py

Lee el diseño (casos_diseno.py), lo que se registró al ejecutar
(ejecucion/TC-0NN.json), los defectos (bugs/BUG-0NN.json) y las capturas
(evidencias/). Los casos se vuelcan en las tablas de la plantilla oficial del
curso (Plantilla_TC_Unificada_TQA.docx), copiadas tal cual, y el documento
principal sigue el formato de Documento_Plantilla_TQA.docx (A4, márgenes 3 cm).
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.table import Table

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import casos_diseno as D  # noqa: E402

PLANTILLA_TC = Path(r"C:\Users\Miscar\Downloads\Plantilla_TC_Unificada_TQA.docx")
PLANTILLA_DOC = Path(r"C:\Users\Miscar\Desktop\septimo semestre\QA\Documento_Plantilla_TQA.docx")
SALIDA = AQUI / "Proyecto_Integrador_Pruebas_Funcionales.docx"

AZUL = RGBColor(0x1F, 0x3A, 0x5F)
GRIS = RGBColor(0x22, 0x22, 0x22)
FILL_CAB = "4472C4"
FILL_ETQ = "D9E2F3"
ESTADOS = ("PASS", "FAIL", "BLOCKED", "NOT RUN")

CASOS = D.CASOS
POR_ID = {c["id"]: c for c in CASOS}
FUNC = {f[0]: f for f in D.FUNCIONALIDADES}


# ─── datos de ejecución ──────────────────────────────────────────────────────
def cargar_ejecucion() -> dict[str, dict]:
    salida = {}
    for c in CASOS:
        p = AQUI / "ejecucion" / f"{c['id']}.json"
        if p.exists():
            salida[c["id"]] = json.loads(p.read_text(encoding="utf-8"))
        else:
            salida[c["id"]] = {"id": c["id"], "resultado": "NOT RUN", "pasos": [], "evidencias": [],
                               "que_ocurrio": "No se ejecutó.", "comparacion": "—", "desviacion": "",
                               "observaciones": "", "fecha_hora": "", "ejecutado_por": ""}
    return salida


def cargar_bugs() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((AQUI / "bugs").glob("BUG-*.json"))]


EJ = cargar_ejecucion()
BUGS = cargar_bugs()
BUG_DE_TC = {}
for b in BUGS:
    BUG_DE_TC.setdefault(b["tc"], []).append(b["id"])


# ─── utilidades de formato ───────────────────────────────────────────────────
def sombrear(celda, color: str) -> None:
    tcPr = celda._tc.get_or_add_tcPr()
    for viejo in tcPr.findall(qn("w:shd")):
        tcPr.remove(viejo)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def poner(celda, texto: str, negrita=False, color=GRIS, tam=8, blanco=False) -> None:
    """Reemplaza el contenido de una celda de la plantilla (Arial 8 como el original)."""
    for p in celda.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    p = celda.paragraphs[0]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    lineas = str(texto).split("\n")
    for i, linea in enumerate(lineas):
        run = p.add_run(linea)
        run.font.name = "Arial"
        run.font.size = Pt(tam)
        run.font.bold = negrita
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if blanco else color
        if i < len(lineas) - 1:
            run.add_break()


def fusionar_derecha(fila, desde: int) -> object:
    celdas = fila.cells
    return celdas[desde].merge(celdas[-1])


def fijar_anchos(tabla: Table, anchos) -> None:
    """Anchos fijos de columna (rejilla + celdas): sin esto Word reparte a su gusto."""
    tabla.autofit = False
    for col, ancho in zip(tabla.columns, anchos):
        col.width = ancho
    for fila in tabla.rows:
        for tc, ancho in zip(fila._tr.tc_lst, anchos):
            tc.get_or_add_tcPr()
            span = tc.tcPr.find(qn("w:gridSpan"))
            n = int(span.get(qn("w:val"))) if span is not None else 1
            i = list(fila._tr.tc_lst).index(tc)
            tc.width = sum(anchos[i:i + n], Cm(0)) if n > 1 else ancho


def borrar_fila(tabla: Table, fila) -> None:
    tabla._tbl.remove(fila._tr)


def tablas_plantilla():
    t = docx.Document(str(PLANTILLA_TC))
    return t.tables[0]._tbl, t.tables[1]._tbl


TBL_DISENO, TBL_EJEC = tablas_plantilla()


ANCHO_UTIL_TWIPS = int((21.0 - 6.0) / 2.54 * 1440)  # A4 menos márgenes de 3 cm


def ajustar_ancho(tbl, ancho=ANCHO_UTIL_TWIPS) -> None:
    """La plantilla de casos es carta con márgenes de 1,5 cm: se escala al texto del documento."""
    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    total = sum(int(c.get(qn("w:w"))) for c in cols)
    k = ancho / total
    for c in cols:
        c.set(qn("w:w"), str(int(int(c.get(qn("w:w"))) * k)))
    for tcw in tbl.iter(qn("w:tcW")):
        if tcw.get(qn("w:type")) in (None, "dxa"):
            tcw.set(qn("w:w"), str(int(int(tcw.get(qn("w:w"))) * k)))
    tblW = tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
    if tblW is not None:
        tblW.set(qn("w:w"), str(ancho))
        tblW.set(qn("w:type"), "dxa")
    ind = tbl.find(qn("w:tblPr")).find(qn("w:tblInd"))
    if ind is not None:
        ind.set(qn("w:w"), "0")


def insertar_tabla(doc, plantilla_tbl) -> Table:
    nuevo = copy.deepcopy(plantilla_tbl)
    ajustar_ancho(nuevo)
    doc.element.body.append(nuevo)
    # mover antes del sectPr final
    sect = doc.element.body.find(qn("w:sectPr"))
    if sect is not None:
        doc.element.body.remove(sect)
        doc.element.body.append(sect)
    return Table(nuevo, doc._body)


# ─── tablas de la plantilla, llenas ──────────────────────────────────────────
def tabla_diseno(doc, c: dict) -> None:
    t = insertar_tabla(doc, TBL_DISENO)
    filas = t.rows
    poner(filas[1].cells[1], c["id"], negrita=True)
    poner(filas[1].cells[3], c["prioridad"])
    poner(filas[2].cells[1], c["titulo"])
    poner(filas[2].cells[3], f'{c["tipo"]}\nTécnica: {D.TECNICAS[c["tecnica"]]}')
    poner(filas[3].cells[1], f'{c["modulo"]} ({FUNC[c["f"]][2]})')
    poner(filas[3].cells[3], D.AMBIENTE)
    poner(filas[4].cells[0], f'¿QUÉ SE QUIERE VALIDAR?  {c["validar"]}', negrita=False)
    poner(filas[5].cells[1], c["estado_inicial"])
    poner(filas[6].cells[1], c["usuario"])
    poner(filas[7].cells[1], c["configuracion"])
    # bloque de datos: como en los casos resueltos de clase (Dato / Valor / Origen / Observación)
    datos = c["datos"]
    for i in (8, 9, 10, 11):
        fusionar_derecha(filas[i], 1)
    poner(filas[8].cells[1], " · ".join(d[0] for d in datos))
    poner(filas[9].cells[1], "\n".join(f"{d[0]}: {d[1]}" for d in datos))
    poner(filas[10].cells[1], "Datos preparados para la prueba en el ambiente local (clínica de demostración)")
    poner(filas[11].cells[1], "\n".join(f"{d[0]} = {d[1]} → {d[2]}" for d in datos if d[2] and d[2] != "—"))
    for i, (accion, dato, esperado) in enumerate(c["pasos"]):
        f = filas[13 + i]
        poner(f.cells[1], accion)
        poner(f.cells[2], dato)
        poner(f.cells[3], esperado)
    poner(filas[20].cells[1], c["exito"])
    # quitar filas de pasos sin usar y las filas vacías del final
    sobrantes = [filas[13 + i] for i in range(len(c["pasos"]), 7)] + [filas[i] for i in range(21, len(filas))]
    for f in sobrantes:
        borrar_fila(t, f)


def tabla_ejecucion(doc, c: dict) -> None:
    e = EJ[c["id"]]
    t = insertar_tabla(doc, TBL_EJEC)
    filas = t.rows
    for i in (1, 2, 3):
        fusionar_derecha(filas[i], 1)
    poner(filas[1].cells[1], c["id"], negrita=True)
    poner(filas[2].cells[1], e.get("ejecutado_por") or "[Integrante del equipo]")
    poner(filas[3].cells[1], e.get("fecha_hora") or "—")
    poner(filas[4].cells[1], D.AMBIENTE)
    poner(filas[4].cells[3], D.VERSION)
    marcas = "    ".join(("☒ " if e["resultado"] == s else "☐ ") + s for s in ESTADOS)
    poner(filas[5].cells[1], marcas, negrita=True)
    poner(filas[6].cells[1], e.get("que_ocurrio", ""))
    poner(filas[7].cells[1], e.get("comparacion", ""))
    pasos = e.get("pasos", [])[:7]
    for i, p in enumerate(pasos):
        f = filas[9 + i]
        poner(f.cells[1], p.get("accion", ""))
        poner(f.cells[2], p.get("estado", ""), negrita=True)
        poner(f.cells[3], p.get("observado", ""))
    evid = e.get("evidencias", [])
    poner(filas[16].cells[1], "\n".join(f'Tipo: Captura  |  Referencia: {x["archivo"]}  |  Descripción: {x["descripcion"]}'
                                        for x in evid) or "—")
    bug = ", ".join(BUG_DE_TC.get(c["id"], [])) or "N/A"
    desv = e.get("desviacion") or ("—" if e["resultado"] == "PASS" else "")
    poner(filas[17].cells[1], f"Desviación encontrada: {desv}    |    Referencia del defecto: {bug}")
    poner(filas[18].cells[1], e.get("observaciones") or "—")
    sobrantes = [filas[9 + i] for i in range(len(pasos), 7)] + [filas[i] for i in range(19, len(filas))]
    for f in sobrantes:
        borrar_fila(t, f)


def tabla_bug(doc, b: dict) -> None:
    filas = [
        ("ID DEL DEFECTO", b["id"], "SEVERIDAD", b["severidad"]),
        ("TÍTULO", b["titulo"], "PRIORIDAD", b["prioridad"]),
        ("CASO QUE LO DETECTÓ", f'{b["tc"]} → FAIL → {b["id"]}', "ESTADO", b.get("estado", "Abierto")),
        ("MÓDULO", b["modulo"], "REQUISITO", FUNC[POR_ID[b["tc"]]["f"]][2]),
        ("AMBIENTE", D.AMBIENTE, "VERSIÓN", D.VERSION),
        ("REPORTADO POR", b.get("reportado_por") or "[Integrante del equipo]", "FECHA", b.get("fecha", "")),
    ]
    largos = [
        ("PRECONDICIONES", b["precondiciones"]),
        ("PASOS PARA REPRODUCIR", "\n".join(b["pasos"])),
        ("DATOS UTILIZADOS", b["datos"]),
        ("RESULTADO ESPERADO", b["esperado"]),
        ("RESULTADO OBTENIDO", b["obtenido"]),
        ("EVIDENCIA", ", ".join(b["evidencias"])),
        ("FRECUENCIA", b["frecuencia"]),
        ("NOTAS", b.get("notas") or "—"),
    ]
    t = doc.add_table(rows=1 + len(filas) + len(largos), cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    anchos = [Cm(3.4), Cm(6.0), Cm(2.4), Cm(3.2)]
    cab = t.rows[0]
    for i, txt in enumerate(("CAMPO", "DETALLE", "CAMPO", "DETALLE")):
        poner(cab.cells[i], txt, negrita=True, blanco=True)
        sombrear(cab.cells[i], FILL_CAB)
    for k, (a, b1, c1, d1) in enumerate(filas, start=1):
        f = t.rows[k]
        for i, (txt, etq) in enumerate(((a, True), (b1, False), (c1, True), (d1, False))):
            poner(f.cells[i], txt, negrita=etq or i == 1 and k == 1)
            if etq:
                sombrear(f.cells[i], FILL_ETQ)
    for k, (etq, txt) in enumerate(largos, start=1 + len(filas)):
        f = t.rows[k]
        poner(f.cells[0], etq, negrita=True)
        sombrear(f.cells[0], FILL_ETQ)
        unida = f.cells[1].merge(f.cells[3])
        poner(unida, txt)
    fijar_anchos(t, anchos)


# ─── texto del documento ─────────────────────────────────────────────────────
def h(doc, texto, nivel=1):
    p = doc.add_heading(texto, level=nivel)
    for r in p.runs:
        r.font.color.rgb = AZUL
        r.font.name = "Arial"
    return p


def par(doc, texto, negrita=False, cursiva=False, tam=11, alinear=None, color=None):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.font.size = Pt(tam)
    run.font.bold = negrita
    run.font.italic = cursiva
    run.font.name = "Arial"
    if color:
        run.font.color.rgb = color
    if alinear:
        p.alignment = alinear
    p.paragraph_format.space_after = Pt(6)
    return p


def viñeta(doc, texto):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(texto)
    run.font.size = Pt(11)
    run.font.name = "Arial"
    return p


def tabla_simple(doc, encabezados, filas, anchos=None, tam=9):
    t = doc.add_table(rows=1 + len(filas), cols=len(encabezados))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, e in enumerate(encabezados):
        poner(t.rows[0].cells[i], e, negrita=True, blanco=True, tam=tam)
        sombrear(t.rows[0].cells[i], FILL_CAB)
    for k, fila in enumerate(filas, start=1):
        for i, v in enumerate(fila):
            negrita = False
            color = GRIS
            if v in ESTADOS:
                negrita = True
                color = {"PASS": RGBColor(0x1E, 0x7B, 0x4F), "FAIL": RGBColor(0xB4, 0x23, 0x18),
                         "BLOCKED": RGBColor(0xA3, 0x5F, 0x00)}.get(v, GRIS)
            poner(t.rows[k].cells[i], v, negrita=negrita, color=color, tam=tam)
    if anchos:
        fijar_anchos(t, [Cm(x) for x in anchos])
    doc.add_paragraph()
    return t


def figura(doc, archivo: str, pie: str, ancho_cm=15.0):
    ruta = AQUI / "evidencias" / archivo
    if not ruta.exists():
        par(doc, f"[Falta la evidencia {archivo}]", cursiva=True, color=RGBColor(0xB4, 0x23, 0x18))
        return
    doc.add_picture(str(ruta), width=Cm(ancho_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = par(doc, pie, cursiva=True, tam=9, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    p.paragraph_format.space_after = Pt(12)


def salto(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def documento_base():
    """Página como Documento_Plantilla_TQA.docx (A4, márgenes 3 cm).

    Esa plantilla no trae los estilos «Table Grid» ni «List Bullet»: se parte
    del documento base de Word y se copia su formato de página.
    """
    ref = docx.Document(str(PLANTILLA_DOC)).sections[0]
    doc = docx.Document()
    s = doc.sections[0]
    s.page_width, s.page_height = ref.page_width, ref.page_height
    s.left_margin, s.right_margin = ref.left_margin, ref.right_margin
    s.top_margin, s.bottom_margin = ref.top_margin, ref.bottom_margin
    estilo = doc.styles["Normal"]
    estilo.font.name = "Arial"
    estilo.font.size = Pt(11)
    return doc


# ─── métricas ────────────────────────────────────────────────────────────────
def metricas():
    conteo = Counter(EJ[c["id"]]["resultado"] for c in CASOS)
    ejecutados = sum(conteo[s] for s in ("PASS", "FAIL"))
    return conteo, ejecutados


def construir():
    doc = documento_base()
    conteo, ejecutados = metricas()
    total = len(CASOS)
    pct = lambda n, d: f"{100 * n / d:.1f} %" if d else "—"  # noqa: E731

    # Portada
    for _ in range(3):
        doc.add_paragraph()
    par(doc, "UNIVERSIDAD PRIVADA FRANZ TAMAYO (UNIFRANZ)", negrita=True, tam=14, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "Testing y Aseguramiento de la Calidad (TQA)", tam=12, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()
    par(doc, "PROYECTO INTEGRADOR", negrita=True, tam=18, alinear=WD_ALIGN_PARAGRAPH.CENTER, color=AZUL)
    par(doc, "Entregable 1 · Pruebas Funcionales", negrita=True, tam=16, alinear=WD_ALIGN_PARAGRAPH.CENTER, color=AZUL)
    doc.add_paragraph()
    par(doc, "Sistema: Fetal Medical Bolivia — historia clínica perinatal con apoyo de inteligencia artificial",
        tam=12, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(4):
        doc.add_paragraph()
    par(doc, "Integrantes: [Nombres del equipo]", tam=12, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "Docente: [Nombre del docente]", tam=12, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    par(doc, "La Paz, Bolivia · octubre de 2026", tam=12, alinear=WD_ALIGN_PARAGRAPH.CENTER)
    salto(doc)

    # 1. Pruebas funcionales
    h(doc, "1. Pruebas funcionales")
    h(doc, "1.1 Objetivo", 2)
    par(doc, "Validar que las funcionalidades principales de Fetal Medical Bolivia cumplen sus requisitos funcionales, "
             "mediante casos de prueba diseñados antes de ejecutar, ejecutados sobre el sistema en marcha y analizados "
             "por el equipo. Este entregable abarca solo pruebas funcionales de caja negra; las pruebas de carga, "
             "rendimiento, usabilidad y automatización se trabajarán en entregables posteriores.")
    h(doc, "1.2 Ambiente de prueba", 2)
    tabla_simple(doc, ["Elemento", "Detalle"], [
        ["Sistema", "Fetal Medical Bolivia: React 18 + Ant Design (interfaz), Django 6 + DRF (API), PostgreSQL 18, "
                    "Redis, servicio de IA en FastAPI"],
        ["Ambiente", D.AMBIENTE + "; http://localhost:3000"],
        ["Versión", D.VERSION],
        ["Datos", "Clínica de demostración «clinica_demo» con datos ficticios; datos propios de cada caso indicados en él"],
        ["Navegador", "Chromium 1366 × 768, tema claro"],
        ["Equipo", "Windows 11 Pro, GPU NVIDIA RTX 3090 para el servicio de IA"],
    ], anchos=[3.5, 11.5])
    h(doc, "1.3 Funcionalidades y criterios de aceptación", 2)
    par(doc, f"Se seleccionaron {len(D.FUNCIONALIDADES)} funcionalidades principales del sistema, cada una ligada a un "
             "requisito funcional del documento de requisitos (docs/sistema/02_requisitos_funcionales.md).")
    for fid, nombre, req, que_hace, criterios in D.FUNCIONALIDADES:
        p = par(doc, f"{fid} · {nombre} ({req})", negrita=True)
        p.paragraph_format.space_after = Pt(2)
        par(doc, que_hace, tam=10)
        for cr in criterios:
            viñeta(doc, cr)
    h(doc, "1.4 Técnicas de diseño utilizadas", 2)
    uso = Counter(c["tecnica"] for c in CASOS)
    tabla_simple(doc, ["Técnica", "Casos", "Cómo se aplicó"], [
        [D.TECNICAS["PE"], str(uso["PE"]),
         "Se separaron las entradas en clases válidas e inválidas y se probó un representante de cada una: credencial "
         "correcta / contraseña errónea / correo inexistente (TC-002); búsqueda con tilde, sin tilde, con otra grafía y "
         "sin coincidencias (TC-011); paciente con y sin consentimiento (TC-007, TC-008)."],
        [D.TECNICAS["VL"], str(uso["VL"]),
         "Se probaron los valores en el límite y justo al lado: 4 y 5 intentos fallidos (TC-003); PA 139/89 y 140/90 "
         "(TC-015, TC-016); FCF 109/110/160/161 (TC-017); IMC 18,4/18,5/25,0/30,0 (TC-019); hemoglobina "
         "11,9/12,0/16,0/16,1/6,9 (TC-022); peso del recién nacido 299/300/6.000/6.001 g (TC-023); fechas hoy y mañana "
         "(TC-010, TC-014)."],
        [D.TECNICAS["TD"], str(uso["TD"]),
         "Se combinaron condiciones y se fijó la acción de cada regla: diabetes gestacional con 4 reglas de la PTOG "
         "(TC-020); alertas del control prenatal con PA, proteinuria y FCF (TC-018); módulo permitido, quitado o ajeno "
         "en un cargo (TC-006)."],
        [D.TECNICAS["CU"], str(uso["CU"]),
         "Flujo principal completo del usuario: primer ingreso con MFA (TC-004), análisis de ecografía con IA (TC-025), "
         "clasificación de una cardiotocografía (TC-028)."],
    ], anchos=[3.8, 1.4, 9.8])
    h(doc, "1.5 Datos de prueba y cobertura", 2)
    par(doc, "Se usaron datos válidos, inválidos y de borde preparados para cada caso: cédulas reservadas para las "
             "pruebas (9100701, 9100801, 9101001), cuentas de prueba creadas por el administrador "
             "(tc003.bloqueo@pruebas.test, tc004.medico@pruebas.test, tc006.obstetriz@pruebas.test), fechas relativas a "
             "la fecha de ejecución y archivos reales de ecografía y cardiotocografía que no se usaron para entrenar las "
             "redes. Todos los datos de pacientes son ficticios.")
    par(doc, f"Cobertura: las {len(D.FUNCIONALIDADES)} funcionalidades seleccionadas tienen al menos un caso positivo y "
             "uno negativo o de valor límite; se cubren los requisitos " +
        ", ".join(sorted({r.strip() for f in D.FUNCIONALIDADES for r in f[2].split("·")}, key=lambda s: (s[:3], int(s.split('-')[1])))) + ".")
    salto(doc)

    # 2. Casos de prueba
    h(doc, "2. Casos de prueba")
    par(doc, f"Se diseñaron {total} casos de prueba con la plantilla del curso (Plantilla de Casos de Prueba, Parte 1). "
             "El resultado esperado de cada uno se fijó antes de ejecutar, a partir del requisito o de la norma clínica "
             "que el requisito cita. Resumen:")
    tabla_simple(doc, ["ID", "Título", "Func.", "Técnica", "Tipo", "Prior."],
                 [[c["id"], c["titulo"], c["f"], c["tecnica"], c["tipo"], c["prioridad"]] for c in CASOS],
                 anchos=[1.5, 6.6, 1.2, 1.4, 3.2, 1.3], tam=8)
    par(doc, "PE = partición de equivalencia · VL = valores límite · TD = tabla de decisión · CU = caso de uso.", tam=9,
        cursiva=True)
    h(doc, "2.1 Casos representativos", 2)
    for ej in ("TC-016", "TC-020"):
        par(doc, f"{ej} · {POR_ID[ej]['titulo']}", negrita=True)
        tabla_diseno(doc, POR_ID[ej])
        doc.add_paragraph()
    par(doc, "Ver Anexo A – Casos de Prueba (los 28 casos completos).", cursiva=True)
    salto(doc)

    # 3. Ejecución
    h(doc, "3. Ejecución")
    fechas = sorted({EJ[c["id"]].get("fecha_hora", "")[:10] for c in CASOS if EJ[c["id"]].get("fecha_hora")})
    par(doc, f"Los casos se ejecutaron sobre el sistema en marcha ({D.AMBIENTE}) el "
             f"{' y '.join(fechas) if fechas else '[fecha]'}, registrando cada paso con la plantilla del curso (Parte 2: "
             "Ejecución) y una captura de pantalla como evidencia. Resultado por caso:")
    tabla_simple(doc, ["ID", "Título", "Resultado", "Defecto"],
                 [[c["id"], c["titulo"], EJ[c["id"]]["resultado"], ", ".join(BUG_DE_TC.get(c["id"], [])) or "—"]
                  for c in CASOS], anchos=[1.5, 9.5, 2.0, 2.0], tam=8)
    h(doc, "3.1 Ejecuciones representativas", 2)
    representativos = ["TC-016", "TC-019"]  # uno que pasa y uno que falla (el más claro de ver)
    for ej in representativos:
        par(doc, f"{ej} · {POR_ID[ej]['titulo']}", negrita=True)
        tabla_ejecucion(doc, POR_ID[ej])
        evid = EJ[ej].get("evidencias", [])
        if evid:
            figura(doc, evid[-1]["archivo"], f'{ej} — {evid[-1]["descripcion"]}', ancho_cm=14.5)
    par(doc, "Ver Anexo B – Evidencias de Ejecución (las 28 ejecuciones con sus capturas).", cursiva=True)
    salto(doc)

    # 4. Defectos y resultados
    h(doc, "4. Defectos y resultados")
    h(doc, "4.1 Resumen de la ejecución", 2)
    tabla_simple(doc, ["Métrica", "Valor"], [
        ["Casos diseñados", str(total)],
        ["Casos ejecutados (PASS + FAIL)", f"{ejecutados} ({pct(ejecutados, total)})"],
        ["PASS", f"{conteo['PASS']} ({pct(conteo['PASS'], ejecutados)} de los ejecutados)"],
        ["FAIL", f"{conteo['FAIL']} ({pct(conteo['FAIL'], ejecutados)} de los ejecutados)"],
        ["BLOCKED", str(conteo["BLOCKED"])],
        ["NOT RUN", str(conteo["NOT RUN"])],
        ["Defectos reportados", str(len(BUGS))],
    ], anchos=[7.0, 8.0])
    if BUGS:
        h(doc, "4.2 Defectos encontrados", 2)
        tabla_simple(doc, ["Defecto", "Caso", "Título", "Severidad", "Prioridad", "Estado"],
                     [[b["id"], b["tc"], b["titulo"], b["severidad"], b["prioridad"], b.get("estado", "Abierto")]
                      for b in BUGS], anchos=[1.7, 1.5, 7.4, 1.7, 1.6, 1.4], tam=8)
        par(doc, "Ver Anexo C – Bug Reports.", cursiva=True)
    h(doc, "4.3 Análisis de los resultados", 2)
    for parrafo in ANALISIS:
        par(doc, parrafo)
    h(doc, "4.4 Matriz de trazabilidad", 2)
    par(doc, "Requisito → Funcionalidad → Caso de prueba → Resultado → Defecto.")
    filas = []
    for fid, nombre, req, *_ in D.FUNCIONALIDADES:
        for c in [c for c in CASOS if c["f"] == fid]:
            filas.append([req, f"{fid} {nombre}", c["id"], EJ[c["id"]]["resultado"],
                          ", ".join(BUG_DE_TC.get(c["id"], [])) or "—"])
    tabla_simple(doc, ["Requisito", "Funcionalidad", "Caso", "Resultado", "Defecto"], filas,
                 anchos=[2.6, 6.4, 1.7, 2.0, 2.3], tam=8)
    salto(doc)

    # 5. Conclusiones
    h(doc, "5. Conclusiones")
    for parrafo in CONCLUSIONES:
        viñeta(doc, parrafo)
    salto(doc)

    # Anexos
    h(doc, "Anexo A – Casos de Prueba")
    par(doc, "Plantilla del curso, Parte 1 · Diseño del caso de prueba. Un caso por tabla.", cursiva=True, tam=10)
    for c in CASOS:
        p = par(doc, f"{c['id']} · {c['titulo']}", negrita=True, tam=10)
        p.paragraph_format.keep_with_next = True
        tabla_diseno(doc, c)
        doc.add_paragraph()
    salto(doc)
    h(doc, "Anexo B – Evidencias de Ejecución")
    par(doc, "Plantilla del curso, Parte 2 · Ejecución del caso de prueba, seguida de sus capturas.", cursiva=True,
        tam=10)
    for c in CASOS:
        p = par(doc, f"{c['id']} · {c['titulo']}", negrita=True, tam=10)
        p.paragraph_format.keep_with_next = True
        tabla_ejecucion(doc, c)
        for x in EJ[c["id"]].get("evidencias", []):
            figura(doc, x["archivo"], f'{x["archivo"]} — {x["descripcion"]}', ancho_cm=13.5)
        doc.add_paragraph()
    if BUGS:
        salto(doc)
        h(doc, "Anexo C – Bug Reports")
        for b in BUGS:
            p = par(doc, f"{b['id']} · {b['titulo']}", negrita=True, tam=10)
            p.paragraph_format.keep_with_next = True
            tabla_bug(doc, b)
            for archivo in b["evidencias"]:
                figura(doc, archivo, f"{archivo} — evidencia de {b['id']}", ancho_cm=13.5)
            doc.add_paragraph()

    doc.save(str(SALIDA))
    print(f"Escrito {SALIDA.name}: {total} casos, {dict(conteo)}, {len(BUGS)} defectos")


# Texto de análisis y conclusiones: se escribe DESPUÉS de ejecutar, en analisis.json
_ANALISIS = AQUI / "analisis.json"
_texto = json.loads(_ANALISIS.read_text(encoding="utf-8")) if _ANALISIS.exists() else {}
ANALISIS = _texto.get("analisis", ["[Análisis pendiente: se redacta con los resultados de la ejecución.]"])
CONCLUSIONES = _texto.get("conclusiones", ["[Conclusiones pendientes.]"])

if __name__ == "__main__":
    construir()
