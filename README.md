# Control de Insumos Críticos — SIMET-USACH

App en Streamlit + SQLite para registrar ingresos/egresos de insumos críticos del
laboratorio, calcular su stock mínimo y clasificación ABC automáticamente, y
mostrar alertas de reposición y de ventana de compra — implementando 1:1 la
metodología del Capítulo 4 de la tesis.

## Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

O más simple: doble clic en `Abrir_App.bat` (o en el acceso directo del
Escritorio si ya lo creaste) — abre el servidor local y la app en el
navegador sin usar la terminal.

La primera vez que corre, crea automáticamente `data/insumos.db` y la llena con
los 61 insumos de `Control_Insumos_Consolidado_SIMET-USACH.xlsx` (hoja "Catálogo
de Insumos"). Si ya existe una base de datos de una versión anterior, sus
columnas se migran solas al esquema nuevo.

## Clasificación ABC y stock mínimo (Capítulo 4)

- **Clasificación ABC multicriterio**: 4 criterios (costo unitario, frecuencia
  de uso, impacto operacional, tiempo de reposición) con pesos AHP fijos —
  Costo 4,11% / Frecuencia 31,29% / Impacto 56,91% / Tiempo de reposición
  7,69%. La clase se asigna por **percentil de posición en el ranking**: el
  20% superior es Clase A, el siguiente 30% es Clase B, el 50% restante es
  Clase C (`abc_scoring.py`). Solo se calcula cuando el insumo tiene los 4
  criterios completos.
- **Stock mínimo** (`stock_calc.py`): se calcula solo, no se edita a mano —
  `CEILING((frecuencia_mensual/30 × tiempo_reposición) × (1 + factor de
  seguridad), unidades_por_cambio)`. El factor de seguridad depende de la
  clase ABC (A=50%, B=30%, C=15%) y el resultado se redondea hacia arriba al
  múltiplo exacto del tamaño del set de reposición.
- **Stock actual**: nunca se escribe a mano — se calcula solo, sumando todos
  los ingresos y restando todos los egresos registrados para ese insumo.
- **Alerta de nivel de stock**: 🔴 "REPONER AHORA" cuando stock actual ≤
  stock mínimo, si no 🟢 "OK".
- **Alerta de ventana de compra**: proyecta la fecha en que el stock caerá al
  mínimo (según el ritmo de consumo mensual) y la compara con la ventana de
  facturación SDT-USACH (día 1 al 20 de cada mes). Si el día proyectado cae
  después del 20, queda 🟠 "FUERA DE VENTANA".

Editar los criterios ABC, la unidad por cambio, el costo o la frecuencia de uso
en **Ver Estado** y guardar recalcula automáticamente el stock mínimo, la
clase ABC y ambas alertas para todo el catálogo (`recalculo.py`).

## Lector de código de barras

Cada insumo tiene un código único (formato `INS0001`, autogenerado — sin
guion, para evitar problemas de layout de teclado con lectores USB). En **Ver
estado** hay un botón para generar los códigos faltantes y otro para descargar
un PDF con etiquetas de código de barras (Code128) listas para imprimir y
pegar en cada insumo. En **Registrar ingreso** y **Registrar egreso** hay un
campo "Escanear código de barras": al escanear con cualquier lector USB
(funciona como teclado) selecciona automáticamente el insumo correspondiente.
También puedes seleccionar el insumo manualmente sin escanear nada.

## Usuarios y trazabilidad

El campo "Responsable" de **Registrar egreso** es una lista predefinida de
iniciales del personal del laboratorio (precargada en la base de datos). Si
alguien no está en la lista, se elige "➕ Otro (nuevo)" y se escribe su nombre
o iniciales — queda guardado para la próxima vez. Hay además un campo opcional
"RAM asociado" para dejar constancia del folio de la Resolución de Aprobación
de Muestra cuando corresponda (la app no se integra con el ERP; esta es la
forma en que queda registrada esa trazabilidad). Al elegir un insumo también
se muestra quién fue la última persona que lo retiró, cuándo y para qué
ensayo/OT.

## Acceso restringido: agregar insumos nuevos

Solo quien tenga la contraseña de administrador puede usar el formulario
"➕ Agregar nuevo insumo" en Ver Estado — todo lo demás (ingresos, egresos,
ver estado, escanear, editar campos del catálogo) queda disponible para
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
3. **Ver estado** — catálogo ordenado por clase ABC (A primero), con ubicación
   física, alerta de nivel de stock y alerta de ventana de compra. Permite
   editar categoría, operación, unidad, ubicación, proveedor, costo, unidades
   por cambio, frecuencia de uso, rendimiento, impacto operacional, tiempo de
   reposición y fuente del dato; el stock mínimo y la clasificación ABC se
   recalculan solos al guardar. Incluye exportar a Excel, generar/descargar
   etiquetas de código de barras, y el formulario restringido para agregar
   insumos nuevos.

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

- `db.py` — esquema SQLite (con migración automática de columnas nuevas) y funciones de acceso a datos.
- `abc_scoring.py` — clasificación ABC multicriterio (pesos AHP + percentil de ranking).
- `stock_calc.py` — stock mínimo, alerta de nivel de stock y alerta de ventana de compra.
- `recalculo.py` — recalcula y guarda ABC + stock mínimo para todo el catálogo.
- `bootstrap.py` — garantiza que la base exista, esté migrada y sembrada, sin importar por qué pantalla se entre primero.
- `seed_from_excel.py` — carga inicial desde `Control_Insumos_Consolidado_SIMET-USACH.xlsx`.
- `scan_ui.py` — selector de insumo con campo de escaneo de código de barras.
- `labels.py` — genera el PDF de etiquetas de código de barras.
- `auth.py` — gate de contraseña de administrador (vía `st.secrets`).
- `app.py` + `pages/` — app Streamlit multipágina.
