"""Modelo de casos de uso de Fetal Medical Bolivia (UML 2.5, convenciones de StarUML).

Reglas que sigue el modelo:
  · Actores PRIMARIOS (inician sus casos de uso) a la IZQUIERDA del sistema;
    actores SECUNDARIOS (sistemas externos que el sistema usa) a la DERECHA,
    con el estereotipo «system».
  · «Usuario del sistema» es un actor ABSTRACTO (nombre en cursiva): nadie lo
    es directamente; todos los roles lo especializan.
  · La herencia entre actores sigue los permisos reales del sistema
    (Backend/usuarios/permisos_por_rol.py): Recepción ⊂ Enfermería ⊂ Médico ⊂
    Administrador, y el Médico también hereda del Laboratorista. Se dibuja en
    su propio diagrama («Jerarquía de actores») para no llenar de líneas el
    diagrama general.
  · «include»: flecha del caso base al incluido (siempre ocurre).
    «extend»: flecha del extensor al caso base, que declara el PUNTO DE
    EXTENSIÓN; la relación lleva su CONDICIÓN.
  · Un mismo caso de uso tiene el mismo identificador y nombre en todos los
    diagramas (es un solo elemento del modelo, con varias vistas).

Cada diagrama fija la posición de sus elementos en una rejilla (columna, fila);
dibujar.py comprueba que ninguna línea se cruce con otra ni pase sobre un caso
de uso o un actor, y se niega a dibujar si ocurre.
"""

# Actores: id → (nombre, tipo, estereotipo, abstracto)
ACTORES = {
    "usuario": ("Usuario del sistema", "primario", None, True),
    "recepcion": ("Recepción", "primario", None, False),
    "enfermera": ("Enfermería", "primario", None, False),
    "lab": ("Laboratorista", "primario", None, False),
    "medico": ("Médico", "primario", None, False),
    "admin": ("Administrador", "primario", None, False),
    "personal": ("Personal de salud", "primario", None, True),
    "ia": ("Servicio de IA", "secundario", "system", False),
}

# Generalización de actores (hijo, padre), igual en todo el modelo
HERENCIA = [("recepcion", "usuario"), ("lab", "usuario"), ("enfermera", "recepcion"), ("medico", "enfermera"),
            ("medico", "lab"), ("admin", "medico"), ("personal", "usuario")]

# Puntos de extensión del caso base: caso base → [(nombre del punto, caso extensor, condición)]
PUNTOS_EXTENSION = {
    "CU-01": [("MFA activo", "CU-04", "el usuario tiene el MFA activado"),
              ("Primer ingreso", "CU-05", "su rol exige MFA y aún no lo configuró"),
              ("Quinto fallo", "CU-06", "5.º intento fallido consecutivo")],
    "CU-25": [("Sin permiso", "CU-26", "el módulo no está en su rol o su cargo")],
    "CU-10": [("Registro exitoso", "CU-30", "se acepta registrar el embarazo ahora")],
    "CU-31": [("Ecografía discordante", "CU-33", "EG por ecografía y por FUM difieren más que el umbral ACOG")],
    "CU-44": [("Alerta detectada", "CU-45", "al menos una alerta clínica")],
    "CU-60": [("Guardar", "CU-66", "el usuario elige guardar el resultado")],
    "CU-72": [("Valor crítico", "CU-73", "el valor cruza el umbral crítico")],
    "CU-71": [("Lote erróneo", "CU-74", "el usuario decide deshacer el lote")],
    "CU-81": [("EG por examen físico", "CU-83", "se necesita la EG del recién nacido")],
    "CU-84": [("Ecografía transperineal", "CU-86", "se dispone de la imagen transperineal")],
    "CU-90": [("Plano de cabeza", "CU-94", "el plano reconocido es la cabeza fetal")],
}

DIAGRAMAS = [
    dict(
        id="general", titulo="Diagrama general de casos de uso", sistema="Fetal Medical Bolivia",
        descripcion="Visión de conjunto. Los actores primarios están a la izquierda y el actor secundario (Servicio "
                    "de IA «system») a la derecha. Cada rol se asocia solo con lo propio de su nivel; lo demás lo "
                    "hereda según la jerarquía de actores (figura siguiente).",
        alto_fila=76, x_limite=330, dist_der=240,
        casos={
            "CU-01": ("Iniciar sesión", 0, 0), "CU-02": ("Cerrar sesión", 0, 1), "CU-11": ("Buscar paciente", 0, 2),
            "CU-10": ("Registrar paciente", 0, 3), "CU-50": ("Agendar cita", 0, 4),
            "CU-40": ("Registrar triaje", 0, 5), "CU-41": ("Registrar control prenatal", 0, 6),
            "CU-60": ("Usar una calculadora clínica", 0, 7),
            "CU-70": ("Registrar resultado de laboratorio", 0, 8),
            "CU-30": ("Registrar embarazo", 0, 9), "CU-90": ("Analizar ecografía obstétrica", 0, 10),
            "CU-95": ("Analizar ecografía ginecológica", 0, 11), "CU-93": ("Clasificar cardiotocografía", 0, 12),
            "CU-80": ("Registrar parto", 0, 13), "CU-B0": ("Consultar centro de reportes", 0, 14),
            "CU-20": ("Gestionar usuarios", 0, 15), "CU-B3": ("Consultar auditoría", 0, 16),
        },
        actores_izq=[("usuario", ["CU-01", "CU-02", "CU-11"]), ("recepcion", ["CU-10", "CU-50"]),
                     ("enfermera", ["CU-40", "CU-41", "CU-60"]), ("lab", ["CU-60", "CU-70"]),
                     ("medico", ["CU-30", "CU-90", "CU-95", "CU-93", "CU-80", "CU-B0"]),
                     ("admin", ["CU-20", "CU-B3"])],
        actores_der=[("ia", ["CU-90", "CU-95"])],
        generalizaciones=[], relaciones=[], puntos=False,
    ),
    dict(
        id="actores", titulo="Jerarquía de actores", sistema=None, tipo="actores",
        descripcion="Generalización de actores: el hijo hereda todos los casos de uso del padre. Refleja la tabla de "
                    "permisos del sistema. «Usuario del sistema» y «Personal de salud» son abstractos (cursiva).",
        posiciones={"usuario": (420, 90), "recepcion": (220, 260), "lab": (620, 260), "personal": (860, 260),
                    "enfermera": (220, 430), "medico": (420, 600), "admin": (420, 770)},
        ancho=1000, alto=880,
    ),
    dict(
        id="autenticacion", titulo="Autenticación y segundo factor", sistema="Fetal Medical Bolivia · Autenticación",
        descripcion="Cualquier usuario inicia sesión; el caso base declara tres puntos de extensión: pedir el código "
                    "MFA, configurarlo en el primer ingreso (médicos y administradores en producción) o bloquear la "
                    "cuenta al quinto intento fallido.",
        alto_fila=96,
        casos={
            "CU-02": ("Cerrar sesión", 0, 0), "CU-01": ("Iniciar sesión", 0, 2.3),
            "CU-03": ("Validar credenciales", 1, 0.8), "CU-04": ("Verificar código MFA", 1, 1.8),
            "CU-05": ("Configurar segundo factor (MFA)", 1, 2.8), "CU-06": ("Bloquear cuenta 15 minutos", 1, 3.8),
            "CU-07": ("Restablecer MFA de un usuario", 0, 5),
        },
        actores_izq=[("usuario", ["CU-02", "CU-01"]), ("admin", ["CU-07"])],
        actores_der=[],
        generalizaciones=[("admin", "usuario")],
        relaciones=[("include", "CU-01", "CU-03"), ("extend", "CU-04", "CU-01"),
                    ("extend", "CU-05", "CU-01"), ("extend", "CU-06", "CU-01")],
    ),
    dict(
        id="acceso", titulo="Control de acceso por rol y cargo", sistema="Fetal Medical Bolivia · Accesos",
        descripcion="El administrador gestiona usuarios y cargos; un cargo solo puede quitar módulos a su rol base. "
                    "Cada vez que el personal usa un módulo, el sistema verifica el permiso del rol y del cargo; en "
                    "el punto «Sin permiso» se extiende con la denegación (403).",
        alto_fila=100,
        casos={
            "CU-20": ("Gestionar usuarios", 0, 0), "CU-21": ("Asignar rol o cargo", 1, 0),
            "CU-22": ("Crear o editar cargo", 0, 1), "CU-23": ("Elegir módulos del rol base", 1, 1),
            "CU-B3": ("Consultar auditoría", 0, 2),
            "CU-24": ("Usar un módulo del sistema", 0, 3.2), "CU-25": ("Verificar permiso del rol y del cargo", 1, 3.2),
            "CU-26": ("Denegar acceso (403)", 2, 3.2),
        },
        actores_izq=[("admin", ["CU-20", "CU-22", "CU-B3"]), ("personal", ["CU-24"])],
        actores_der=[],
        generalizaciones=[],
        relaciones=[("include", "CU-20", "CU-21"), ("include", "CU-22", "CU-23"),
                    ("include", "CU-24", "CU-25"), ("extend", "CU-26", "CU-25")],
    ),
    dict(
        id="pacientes", titulo="Gestión de pacientes", sistema="Fetal Medical Bolivia · Pacientes",
        descripcion="Recepción registra, busca e importa pacientes; Enfermería y el Médico heredan esos casos. El "
                    "registro incluye el consentimiento (Ley 164) y la validación de la cédula, y en el punto "
                    "«Registro exitoso» se extiende con el registro del embarazo.",
        alto_fila=118,
        casos={
            "CU-10": ("Registrar paciente", 0, 0.5), "CU-12": ("Registrar consentimiento (Ley 164)", 1, 0),
            "CU-13": ("Validar cédula única", 1, 1), "CU-30": ("Registrar embarazo", 2, 0.5),
            "CU-11": ("Buscar paciente", 0, 2), "CU-14": ("Ignorar tildes y grafías (Quispe/Kispe)", 1, 2),
            "CU-15": ("Importar pacientes desde Excel", 0, 3), "CU-16": ("Detectar cédulas duplicadas", 1, 3),
        },
        actores_izq=[("recepcion", ["CU-10", "CU-11", "CU-15"]), ("enfermera", []), ("medico", [])],
        actores_der=[],
        generalizaciones=[("enfermera", "recepcion"), ("medico", "enfermera")],
        relaciones=[("include", "CU-10", "CU-12"), ("include", "CU-10", "CU-13"), ("extend", "CU-30", "CU-10"),
                    ("include", "CU-11", "CU-14"), ("include", "CU-15", "CU-16")],
    ),
    dict(
        id="embarazo", titulo="Registro del embarazo", sistema="Fetal Medical Bolivia · Embarazos",
        descripcion="El médico registra el embarazo; el sistema calcula la edad gestacional y la FPP (Naegele) y "
                    "verifica que no haya otro embarazo activo. Si la ecografía discrepa, se redata (ACOG).",
        alto_fila=110,
        casos={
            "CU-30": ("Registrar embarazo", 0, 0.5), "CU-31": ("Calcular EG y FPP (Naegele)", 1, 0),
            "CU-33": ("Redatar según ecografía (ACOG)", 2, 0),
            "CU-32": ("Verificar un solo embarazo activo", 1, 1.1),
            "CU-34": ("Ver embarazo y su línea de tiempo", 0, 2.1),
        },
        actores_izq=[("medico", ["CU-30", "CU-34"])],
        actores_der=[],
        generalizaciones=[],
        relaciones=[("include", "CU-30", "CU-31"), ("include", "CU-30", "CU-32"), ("extend", "CU-33", "CU-31")],
    ),
    dict(
        id="control", titulo="Triaje y control prenatal", sistema="Fetal Medical Bolivia · Control prenatal",
        descripcion="Enfermería registra el triaje y el control prenatal (el Médico hereda estos casos). El control "
                    "incluye los signos vitales y la evaluación de alertas clínicas (PA ≥ 140/90, FCF fuera de "
                    "110–160 lpm, proteinuria…); si hay alerta, se notifica al médico responsable.",
        alto_fila=100,
        casos={
            "CU-40": ("Registrar triaje", 0, 0), "CU-42": ("Asignar prioridad", 1, 0),
            "CU-41": ("Registrar control prenatal", 0, 1.6), "CU-43": ("Registrar signos vitales", 1, 1),
            "CU-44": ("Evaluar alertas clínicas", 1, 2.2), "CU-45": ("Notificar al médico responsable", 2, 2.2),
            "CU-46": ("Ver historial de controles", 0, 3.4),
        },
        actores_izq=[("enfermera", ["CU-40", "CU-41", "CU-46"]), ("medico", [])],
        actores_der=[],
        generalizaciones=[("medico", "enfermera")],
        relaciones=[("include", "CU-40", "CU-42"), ("include", "CU-41", "CU-43"), ("include", "CU-41", "CU-44"),
                    ("extend", "CU-45", "CU-44")],
    ),
    dict(
        id="calculadoras", titulo="Calculadoras clínicas", sistema="Fetal Medical Bolivia · Calculadoras",
        descripcion="Las calculadoras son especializaciones de un mismo caso de uso (generalización de casos de "
                    "uso). Las usan Enfermería y el Laboratorista; el Médico las hereda. El resultado puede guardarse.",
        alto_fila=96,
        casos={
            "CU-60": ("Usar una calculadora clínica", 0, 2), "CU-61": ("Calcular IMC (OMS)", 1, 0),
            "CU-62": ("Diagnosticar diabetes gestacional (PTOG)", 1, 1), "CU-63": ("Calcular puntaje de Bishop", 1, 2),
            "CU-64": ("Estimar riesgo de preeclampsia", 1, 3), "CU-65": ("Calcular edad gestacional", 1, 4),
            "CU-66": ("Guardar en el historial", 0, 4),
        },
        actores_izq=[("enfermera", ["CU-60"]), ("lab", ["CU-60"])],
        actores_der=[],
        generalizaciones=[],
        relaciones=[("gen", "CU-61", "CU-60"), ("gen", "CU-62", "CU-60"), ("gen", "CU-63", "CU-60"),
                    ("gen", "CU-64", "CU-60"), ("gen", "CU-65", "CU-60"), ("extend", "CU-66", "CU-60")],
    ),
    dict(
        id="laboratorio", titulo="Laboratorio", sistema="Fetal Medical Bolivia · Laboratorio",
        descripcion="El Laboratorista registra o importa resultados (el Médico hereda estos casos); cada resultado "
                    "se evalúa contra el rango de referencia del catálogo, un valor crítico genera una alerta y un "
                    "lote importado se puede deshacer. El Administrador mantiene el catálogo.",
        alto_fila=104,
        casos={
            "CU-70": ("Registrar resultado de laboratorio", 0, 0),
            "CU-72": ("Evaluar contra el rango de referencia", 1, 0.8),
            "CU-73": ("Alertar resultado crítico", 2, 0.8),
            "CU-71": ("Importar resultados (Excel o CSV)", 0, 1.7), "CU-74": ("Deshacer un lote importado", 1, 2.6),
            "CU-75": ("Administrar catálogo y rangos", 0, 3.7),
        },
        actores_izq=[("lab", ["CU-70", "CU-71"]), ("medico", []), ("admin", ["CU-75"])],
        actores_der=[],
        generalizaciones=[("medico", "lab")],
        relaciones=[("include", "CU-70", "CU-72"), ("include", "CU-71", "CU-72"), ("extend", "CU-73", "CU-72"),
                    ("extend", "CU-74", "CU-71")],
    ),
    dict(
        id="parto", titulo="Parto y recién nacido", sistema="Fetal Medical Bolivia · Partos",
        descripcion="El médico registra el parto con sus recién nacidos validados, el partograma y la epicrisis. Con "
                    "ecografía transperineal, el Servicio de IA (actor secundario) mide el ángulo de progresión.",
        alto_fila=112,
        casos={
            "CU-80": ("Registrar parto", 0, 0.5), "CU-81": ("Registrar recién nacido", 1, 0),
            "CU-82": ("Validar peso, talla y Apgar", 2, 0), "CU-83": ("Estimar EG por Capurro o Ballard", 1, 1.15),
            "CU-84": ("Registrar tacto en el partograma", 0, 2.3), "CU-85": ("Ver curva de dilatación y líneas OMS", 1, 2.3),
            "CU-86": ("Medir ángulo de progresión", 1, 3.4), "CU-87": ("Redactar y firmar epicrisis", 0, 4.4),
        },
        actores_izq=[("medico", ["CU-80", "CU-84", "CU-87"])],
        actores_der=[("ia", ["CU-86"])],
        generalizaciones=[],
        relaciones=[("include", "CU-80", "CU-81"), ("include", "CU-81", "CU-82"), ("extend", "CU-83", "CU-81"),
                    ("include", "CU-84", "CU-85"), ("extend", "CU-86", "CU-84")],
    ),
    dict(
        id="ia", titulo="Inteligencia artificial", sistema="Fetal Medical Bolivia · IA",
        descripcion="El médico (primario, izquierda) analiza ecografías; el Servicio de IA «system» (secundario, "
                    "derecha) ejecuta las redes: plano anatómico, segmentación y medidas, cribado cerebral y lesiones "
                    "ginecológicas. La cardiotocografía se clasifica en el propio sistema.",
        alto_fila=100, x_limite=300,
        casos={
            "CU-90": ("Analizar ecografía obstétrica", 0, 1.1), "CU-91": ("Reconocer plano anatómico", 1, 0),
            "CU-92": ("Segmentar y medir (HC, ICT, CA, LF)", 1, 1.05), "CU-94": ("Cribar anomalías cerebrales", 1, 2.1),
            "CU-95": ("Analizar ecografía ginecológica", 0, 3.3),
            "CU-96": ("Segmentar y clasificar la lesión", 1, 3.3),
            "CU-93": ("Clasificar cardiotocografía", 0, 4.4), "CU-97": ("Consultar la Guía de IA", 0, 5.4),
        },
        actores_izq=[("medico", ["CU-90", "CU-95", "CU-93", "CU-97"])],
        actores_der=[("ia", ["CU-91", "CU-92", "CU-94", "CU-96"])],
        generalizaciones=[],
        relaciones=[("include", "CU-90", "CU-91"), ("include", "CU-90", "CU-92"), ("extend", "CU-94", "CU-90"),
                    ("include", "CU-95", "CU-96")],
    ),
    dict(
        id="reportes", titulo="Reportes y auditoría", sistema="Fetal Medical Bolivia · Reportes",
        descripcion="El médico consulta reportes y exporta listados; cada exportación queda en la auditoría, que "
                    "solo consulta el Administrador (que además hereda los casos del médico).",
        casos={
            "CU-B0": ("Consultar centro de reportes", 0, 0), "CU-B4": ("Filtrar por período", 1, 0),
            "CU-B1": ("Exportar listado a Excel", 0, 1.5), "CU-B5": ("Registrar en la auditoría", 1, 1.5),
            "CU-B2": ("Generar reporte en PDF", 0, 3), "CU-B3": ("Consultar auditoría", 0, 4.5),
        },
        actores_izq=[("medico", ["CU-B0", "CU-B1", "CU-B2"]), ("admin", ["CU-B3"])],
        actores_der=[],
        generalizaciones=[("admin", "medico")],
        relaciones=[("include", "CU-B0", "CU-B4"), ("include", "CU-B1", "CU-B5")],
    ),
]
