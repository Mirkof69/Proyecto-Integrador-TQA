# Cómo se ejecutan y registran los casos (Entregable 1)

El diseño está en `casos_diseno.py` (ID, datos, pasos y resultado esperado,
fijados ANTES de ejecutar). La ejecución se hace sobre el sistema real en
marcha: http://localhost:3000 (producción local, DEBUG=False), API
http://localhost:8000/api.

## Reglas

1. **Ejecutar de verdad, en la interfaz**, como lo haría la persona usuaria:
   abrir pantallas, llenar formularios, pulsar botones. Se puede manejar el
   navegador con un guion de Playwright para ir paso a paso y tomar capturas,
   pero cada paso debe ser la acción de interfaz que dice el caso. Solo los
   pasos que el caso dice «por la API» se hacen con una petición HTTP desde la
   sesión del navegador.
2. **No modificar el sistema** (ni código, ni configuración, ni base de datos
   por fuera de la interfaz). Si algo falla, se registra; no se arregla. La
   corrección y el re-test son otra actividad del curso.
3. **No cambiar el resultado esperado** después de ver lo que pasa. Si el
   diseño resultó ambiguo o la interfaz es distinta a lo previsto, se dice en
   `observaciones` y se ejecuta lo más fiel posible.
4. Estados: PASS = coincide con lo esperado; FAIL = diferencia verificable;
   BLOCKED = no se pudo ejecutar (precondición imposible, servicio caído…);
   NOT RUN = no se ejecutó.
5. Cada paso tiene su propio estado (PASS / FAIL / N/A) y lo observado.

## Qué deja cada caso

- Capturas en `evidencias/evidencia_TC0NN_MM.png` (MM = 01, 02…), al menos una
  por caso y una en cada paso donde se ve el resultado esperado u obtenido.
  Ventana 1366×768, tema claro.
- Un archivo `ejecucion/TC-0NN.json`:

```json
{
  "id": "TC-0NN",
  "ejecutado_por": "",
  "fecha_hora": "18/10/2026 21:05",
  "resultado": "PASS | FAIL | BLOCKED | NOT RUN",
  "que_ocurrio": "Comportamiento observado, concreto (mensajes literales entre comillas).",
  "comparacion": "¿Coincide con lo esperado? Si no, cuál es la diferencia.",
  "pasos": [
    {"accion": "Acción realizada", "estado": "PASS | FAIL | N/A", "observado": "Qué ocurrió"}
  ],
  "evidencias": [{"archivo": "evidencia_TC0NN_01.png", "descripcion": "Qué demuestra"}],
  "desviacion": "Qué no coincidió (vacío si PASS)",
  "observaciones": "Información adicional relevante"
}
```

- Si el caso da FAIL y hay un defecto: `bugs/borrador_TC-0NN.json`:

```json
{
  "tc": "TC-0NN",
  "titulo": "Resumen corto del defecto",
  "modulo": "…",
  "severidad": "Crítica | Alta | Media | Baja",
  "prioridad": "Alta | Media | Baja",
  "precondiciones": "…",
  "pasos": ["1 …", "2 …"],
  "datos": "…",
  "esperado": "…",
  "obtenido": "…",
  "evidencias": ["evidencia_TC0NN_02.png"],
  "frecuencia": "Siempre | Intermitente (n de m)",
  "notas": "Causa probable si se pudo ver SIN tocar el código (p. ej. respuesta HTTP); si no, vacío"
}
```

`ejecutado_por` queda vacío: lo completa el equipo.
