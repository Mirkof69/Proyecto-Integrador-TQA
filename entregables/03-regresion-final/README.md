# Entregable 3 · Regresión final (21/11/2026)

Ejecución completa de la automatización ([Proyecto-Automatizacion-TQA](https://github.com/Mirkof69/Proyecto-Automatizacion-TQA))
contra el sistema en marcha ([Proyector-historial](https://github.com/Mirkof69/Proyector-historial)) después de
reorganizarlo en microservicios (`backend/`, `frontend/`, `servicio-ia/`, `redes-neuronales/`, `modelos-ia/`).

| Indicador | Valor |
|---|---|
| Corrida | `20261121-031428`, suite completa, Chrome, doble factor activo |
| Casos del catálogo | 181 (8 nuevos: TC-174 a TC-181, configuración y respaldos) |
| Pruebas ejecutadas | 581: 575 PASS · 1 FAIL · 5 NOT RUN |
| Falla | TC-116 (latencia p95 de un listado): pico aislado mientras el servidor generaba un respaldo de 686 MB. Repetida con 40 muestras: 16/16 PASS, p95 entre 28 y 112 ms (criterio < 200 ms) |
| NOT RUN, por diseño | 3 de estrés con Locust (requieren `AUTORIZAR_ESTRES=1`), la restauración real de la base (`AUTORIZAR_RESTAURAR=1`) y la configuración del doble factor en el primer ingreso |

Además de la regresión se verificó:

- Las 13 redes neuronales y los 2 modelos tabulares son idénticos byte a byte a los de antes de la reorganización
  (32 archivos, sha256) y el servicio de IA reproduce lo medido al entrenar (57/57 pruebas).
- Cada red respondió con muestras reales en el sistema en marcha (12 familias).
- Las notificaciones en vivo: una cita agendada por recepción le llega al médico por WebSocket en menos de 200 ms.
- Pruebas propias del sistema: backend 1.177, frontend 145.

Defectos corregidos en esta iteración: cualquier rol podía cambiar los umbrales clínicos de alertas (ahora médico y
administrador), no existía la carga de un respaldo desde otro equipo (agregada) y el respaldo diario quedaba en el
mismo disco que la base (ahora se copia a otro disco).

Archivos: reporte en PDF, Word y HTML de la corrida.
