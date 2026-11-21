# Proyecto Integrador · Testing, Quality Assurance

Documentos, evidencias y entregables del Proyecto Integrador de la materia
**Testing, Quality Assurance (TQA)** — Universidad Privada Franz Tamayo (UNIFRANZ).

**Sistema bajo prueba:** Fetal Medical Bolivia, historia clínica gineco-obstétrica con análisis de ecografías
mediante redes neuronales (React + Django REST + PostgreSQL + microservicio de IA).

**Automatización:** [Proyecto-Automatizacion-TQA](https://github.com/Mirkof69/Proyecto-Automatizacion-TQA)

## Contenido

| Carpeta | Qué hay |
|---|---|
| `entregables/01-pruebas-funcionales/` | **Entregable 1 · Pruebas funcionales**: documento en PDF y Word, 28 casos de prueba con la plantilla del curso, ejecución, 11 bug reports, métricas, matriz de trazabilidad y conclusiones |
| `entregables/01-pruebas-funcionales/anexos/evidencias/` | 176 capturas de la ejecución (Anexo B) |
| `entregables/01-pruebas-funcionales/archivos-de-trabajo/` | Diseño de los casos (`casos_diseno.py`), registro de cada ejecución (`ejecucion/TC-0NN.json`), bug reports (`bugs/BUG-0NN.json`) y el generador del documento |
| `entregables/02-capitulo-6-automatizacion/` | **Entregable 2 · Capítulo 6, Estrategia y ejecución de pruebas**: documento final en PDF (128 hojas) y Word |
| `entregables/03-regresion-final/` | **Entregable 3 · Regresión final (21/11/2026)**: reporte de la corrida completa sobre el sistema reorganizado en microservicios, con la verificación de las redes neuronales y las notificaciones |
| `documentacion/casos-de-uso-uml/` | Casos de uso UML: 12 diagramas, 69 casos de uso y 30 especificaciones (PDF y Word) y el proyecto de **StarUML** (`Casos_de_Uso_FetalMedical.mdj`) |
| `documentacion/` | Versión anterior del Capítulo 6 |

## Resultados del Entregable 1

28 casos diseñados y ejecutados · 20 PASS · 8 FAIL · 0 BLOCKED · 11 defectos
(1 crítico, 4 altos, 6 medios). Las técnicas usadas fueron partición de
equivalencia, valores límite, tabla de decisión y caso de uso; los valores
límite encontraron 7 de los 8 fallos.

## Resultados del Entregable 2 · Capítulo 6

Plan de pruebas, pruebas funcionales, automatización, pruebas no funcionales, ejecución, resultados, conclusiones y
recomendaciones, con datos de ejecuciones reales sobre el sistema en marcha y los cinco roles.

| Indicador | Valor |
|---|---|
| Casos de prueba diseñados | 172 |
| Casos automatizados | 145 de 145 seleccionados (100 %) |
| Por herramienta | 54 API (pytest + requests) · 52 Selenium WebDriver · 35 Selenium IDE · 4 Locust |
| Regresión final (`20261115-091110`) | 572 pruebas: 568 PASS · 0 FAIL · 0 BLOCKED · 4 NOT RUN |
| Porcentaje de salud | 100 % (PASS sobre pruebas ejecutadas) |
| Cobertura de requisitos | 40 de 50 (80 %) |
| Carga con Locust (40 usuarios, 3 min) | 3 352 peticiones · p95 89 ms · 0 % de errores |
| Defectos | 8 encontrados por la automatización: 7 corregidos y verificados, 1 de severidad baja abierto con propuesta |

Los defectos del Capítulo 6 están registrados como *Issues* con la etiqueta
[`capitulo-6`](https://github.com/Mirkof69/Proyecto-Integrador-TQA/issues?q=label%3Acapitulo-6) y el prefijo
**Cap6-**, para distinguirlos de los del Entregable 1. Cada uno tiene pasos, resultado esperado y obtenido, causa raíz,
corrección, commit, retesting y regresión.

## Seguimiento

Las tareas, los bugs y las correcciones se registran como *Issues* y se siguen
en el tablero del proyecto (GitHub Projects): Backlog → To Do → In Progress →
In Review → Done.

## Ramas (gitflow)

| Rama | Uso |
|---|---|
| `main` | Entregas (etiquetas `v2.0.0` y siguientes) |
| `develop` | Integración |
| `feature/*` | Un cambio por rama, con su issue y su pull request hacia `develop` |
| `release/*` | Preparación de cada entrega, unida a `main` y de vuelta a `develop` |

## Equipo

- Mirkof Guzman — [@Mirkof69](https://github.com/Mirkof69)
- [Integrantes del equipo]

Docente: Reynel Sánchez Chuquimia

## Resultados del Entregable 3 · Regresión final

182 casos en el catálogo · 582 pruebas el 21/11/2026: 577 PASS, 0 FAIL y 5 NOT RUN que se corrieron aparte con
autorización (restauración real y estrés, pico y resistencia con Locust: todas PASS, 0 errores en 45.665 peticiones). Detalle en [entregables/03-regresion-final](entregables/03-regresion-final/).
