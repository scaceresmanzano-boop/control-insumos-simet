# Control de Insumos Críticos — SIMET-USACH

App en Streamlit + SQLite para registrar ingresos/egresos de insumos críticos del
laboratorio y visualizar el estado de stock ordenado por clasificación ABC.

## Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

La primera vez que corre, crea automáticamente `data/insumos.db` y la llena con
los 36 insumos del Excel `Clasificacion_ABC_Multicriterio_SIMET-USACH_1.xlsx`
(solo ID y nombre — el resto de los campos se completan desde la pantalla
**Ver estado**) y con las 12 filas de referencia del Excel
`Ficha_Consumo_Operaciones_SIMET-USACH_2.xlsx`.

## Pantallas

1. **Registrar ingreso** — suma stock (compra recibida).
2. **Registrar egreso** — descuenta stock, valida que haya disponible antes de confirmar.
3. **Ver estado** — catálogo ordenado por clase ABC (A primero), con alerta
   🔴/🟠/🟢 según el stock frente al mínimo definido. Permite editar stock
   mínimo, proveedor, unidad y los 4 criterios de clasificación ABC (costo,
   frecuencia de uso, impacto operacional, tiempo de reposición); al guardar,
   la clasificación ABC se recalcula para todo el catálogo con la misma
   metodología (Hadi-Vencheh) del Excel original. Incluye botón para exportar
   el estado actual a Excel.

## Nota sobre Streamlit Community Cloud

El almacenamiento de Streamlit Community Cloud **no es persistente**: si la
app se reinicia (por inactividad, redeploy o mantenimiento), el sistema de
archivos vuelve al estado del último commit en GitHub y se pierden los
cambios hechos solo en `data/insumos.db` desde la última vez que se subió a
git. Para uso diario real de seguimiento de stock del laboratorio se
recomienda correr la app localmente (o en un servidor propio). El link de
Streamlit Cloud es útil para compartir una vista del sistema con el equipo,
pero conviene subir periódicamente `data/insumos.db` a git (o migrar a una
base persistente externa) si se va a operar desde ahí de forma continua.

## Estructura

- `db.py` — esquema SQLite y funciones de acceso a datos.
- `abc_scoring.py` — cálculo de clasificación ABC multicriterio.
- `seed_from_excel.py` — carga inicial desde los dos Excel de la tesis.
- `app.py` + `pages/` — app Streamlit multipágina.
