# Control de Insumos Críticos — SIMET-USACH

App en Streamlit + SQLite para registrar ingresos/egresos de insumos críticos del
laboratorio y visualizar el estado de stock ordenado por clasificación ABC.

## Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

O más simple: doble clic en `Abrir_App.bat` (o en el acceso directo del
Escritorio si ya lo creaste) — abre el servidor local y la app en el
navegador sin usar la terminal.

La primera vez que corre, crea automáticamente `data/insumos.db` y la llena con
los 36 insumos del Excel `Clasificacion_ABC_Multicriterio_SIMET-USACH_1.xlsx`
(solo ID y nombre — el resto de los campos se completan desde la pantalla
**Ver estado**) y con las 12 filas de referencia del Excel
`Ficha_Consumo_Operaciones_SIMET-USACH_2.xlsx`.

## Lector de código de barras

Cada insumo tiene un código único (formato `INS-0001`, autogenerado). En **Ver
estado** hay un botón para generar los códigos faltantes y otro para descargar
un PDF con etiquetas de código de barras (Code128) listas para imprimir y
pegar en cada insumo. En **Registrar ingreso** y **Registrar egreso** hay un
campo "Escanear código de barras": al escanear con cualquier lector USB
(funciona como teclado) selecciona automáticamente el insumo correspondiente.
También puedes seleccionar el insumo manualmente sin escanear nada.

## Usuarios

El campo "Responsable" de **Registrar egreso** es una lista predefinida de
iniciales del personal del laboratorio (precargada en la base de datos). Si
alguien no está en la lista, se elige "➕ Otro (nuevo)" y se escribe su nombre
o iniciales — queda guardado para la próxima vez. Al elegir un insumo también
se muestra quién fue la última persona que lo retiró, cuándo y para qué
ensayo/OT.

## Acceso restringido: agregar insumos nuevos

Solo quien tenga la contraseña de administrador puede usar el formulario
"➕ Agregar nuevo insumo" en Ver Estado — todo lo demás (ingresos, egresos,
ver estado, escanear, editar stock/proveedor/ABC) queda disponible para
cualquiera. La contraseña se configura así (nunca se sube a git):

- **Local**: copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml`
  y cambia el valor de `admin_password`.
- **Streamlit Cloud**: en tu app → Manage app → Settings → Secrets, pega:
  ```
  admin_password = "tu-clave"
  ```
  (debe ser la misma clave que uses localmente si quieres que funcione igual
  en ambos lados).

## Pantallas

1. **Registrar ingreso** — suma stock (compra recibida).
2. **Registrar egreso** — descuenta stock, valida que haya disponible antes de confirmar.
3. **Ver estado** — catálogo ordenado por clase ABC (A primero), con alerta
   🔴/🟠/🟢 según el stock frente al mínimo definido. Permite editar stock
   mínimo, proveedor, unidad y los 4 criterios de clasificación ABC (costo,
   frecuencia de uso, impacto operacional, tiempo de reposición); al guardar,
   la clasificación ABC se recalcula para todo el catálogo con la misma
   metodología (Hadi-Vencheh) del Excel original. Incluye botón para exportar
   el estado actual a Excel, y un formulario **➕ Agregar nuevo insumo** para
   incorporar ítems que no vinieron en el Excel original.

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
