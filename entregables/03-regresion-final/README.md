# Entregable 3 · Regresión final (21/11/2026)

Ejecución completa de la automatización ([Proyecto-Automatizacion-TQA](https://github.com/Mirkof69/Proyecto-Automatizacion-TQA))
contra el sistema en marcha ([Proyector-historial](https://github.com/Mirkof69/Proyector-historial)) reorganizado en
microservicios (`backend/`, `frontend/`, `servicio-ia/`, `redes-neuronales/`, `modelos-ia/`).

## Regresión completa

| Indicador | Valor |
|---|---|
| Corrida | `20261121-110601`, suite completa, Chrome, doble factor activo |
| Casos del catálogo | 182 (9 nuevos: TC-174 a TC-182, configuración, respaldos e historia clínica) |
| Pruebas | 582: **577 PASS · 0 FAIL** · 5 NOT RUN que exigen autorización y se corrieron aparte |
| Corridas autorizadas aparte | Restauración real de la base (TC-180): PASS. Estrés, pico y resistencia (TC-113 a TC-115): PASS |

## Rendimiento (Locust, carpeta `rendimiento/`)

| Prueba | Peticiones | Errores | Resultado |
|---|---|---|---|
| Resistencia: 40 usuarios durante 15 minutos | 16.394 | 0 | p50 24 ms, p95 73 ms, sin degradación |
| Estrés: escalones de 20 usuarios hasta 200 | 24.659 | 0 | p95 < 250 ms hasta 100 usuarios; rendimiento máximo ≈ 58 peticiones/s hacia 160 usuarios; p95 1,8 s con 200 |
| Pico: de 10 a 150 usuarios de golpe | 4.612 | 0 | Absorbe el salto sin errores |

## Inteligencia artificial

- Las 13 redes y los 2 modelos tabulares son idénticos byte a byte a los de antes de la reorganización (32 archivos,
  sha256) y el servicio de IA reproduce lo medido al entrenar (57/57 pruebas).
- Muestras reales por el sistema en marcha en 12 familias de redes (clasificación, segmentación, regresión y puntos):
  el comportamiento coincide con las métricas publicadas (por ejemplo, ovario 3 de 5, como su 68,6 %).

## Defectos corregidos en esta iteración

| Defecto | Corrección |
|---|---|
| Cualquier rol podía cambiar los umbrales clínicos de alertas | Solo médico y administrador (TC-176) |
| No se podía cargar un respaldo descargado | Carga validada de respaldos `.sql` (TC-178) |
| El respaldo diario quedaba en el mismo disco que la base | Copia automática a otro disco |
| Historia clínica: la nota SOAP, la receta y la exportación solo se simulaban; las citas nunca se mostraban y las notas salían sin texto | Guardado real, datos reales en cada pestaña y actualización en vivo (TC-182) |

Pruebas propias del sistema: backend 1.180, frontend 145, servicio de IA 57.

Archivos: reporte de la regresión en PDF, Word y HTML, y los reportes de Locust con su resumen.
