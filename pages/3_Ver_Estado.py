from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

import db
from auth import requiere_admin
from bootstrap import asegurar_base_lista
from db import CATEGORIAS
from labels import generar_pdf_etiquetas
from recalculo import recalcular_catalogo
from stock_calc import calcular_alertas

st.set_page_config(page_title="Ver estado", page_icon="📊", layout="wide")
st.title("📊 Estado de insumos")

asegurar_base_lista()
conn = db.get_connection()

with st.expander("➕ Agregar nuevo insumo (solo SCM)"):
    if requiere_admin("agregar insumos nuevos"):
        with st.form("form_nuevo_insumo", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                nombre_nuevo = st.text_input("Nombre del insumo *")
                categoria_nueva = st.selectbox("Categoría", options=[""] + CATEGORIAS)
                operacion_nueva = st.text_input("Operación asociada")
                ubicacion_nueva = st.text_input("Ubicación (estante/repisa/zona)")
            with col_b:
                unidad_nueva = st.text_input("Unidad (ej. unidad, litro, kg)")
                costo_nuevo = st.number_input("Costo unitario (CLP)", min_value=0.0, step=1.0)
                unidades_por_cambio_nuevo = st.number_input(
                    "N° unidades por cambio de set", min_value=1.0, step=1.0, value=1.0
                )
                proveedor_nuevo = st.text_input("Proveedor")
            with col_c:
                frecuencia_nueva = st.number_input("Frecuencia de uso mensual", min_value=0.0, step=1.0)
                tiempo_rep_nuevo = st.number_input("Tiempo de reposición (días)", min_value=0.0, step=1.0)
                rendimiento_nuevo = st.number_input("Rendimiento (probetas/cambio)", min_value=0.0, step=1.0)
                fuente_dato_nueva = st.text_input("Fuente del dato (rendimiento)")

            stock_inicial = st.number_input("Stock inicial (ingreso de apertura)", min_value=0.0, step=1.0, format="%g")
            definir_abc = st.checkbox("Definir criterios de clasificación ABC ahora (costo, frecuencia, impacto, tiempo)")
            impacto_nuevo = None
            if definir_abc:
                impacto_nuevo = st.number_input("Impacto operacional (1-5)", min_value=1, max_value=5, step=1)

            agregar = st.form_submit_button("Agregar insumo")

            if agregar:
                try:
                    nuevo_id = db.crear_insumo(
                        conn, nombre_nuevo,
                        categoria=categoria_nueva or None,
                        operacion=operacion_nueva or None,
                        unidad=unidad_nueva or None,
                        proveedor=proveedor_nuevo or None,
                        costo_unitario=costo_nuevo or None,
                        unidades_por_cambio=unidades_por_cambio_nuevo or None,
                        frecuencia_uso_mensual=frecuencia_nueva or None,
                        rendimiento_probetas=rendimiento_nuevo or None,
                        impacto_operacional=impacto_nuevo if definir_abc else None,
                        tiempo_reposicion_dias=tiempo_rep_nuevo or None,
                        fuente_dato=fuente_dato_nueva or None,
                        ubicacion=ubicacion_nueva or None,
                    )
                    if stock_inicial > 0:
                        db.registrar_ingreso(conn, nuevo_id, stock_inicial, "Carga inicial", date.today().isoformat())
                    recalcular_catalogo(conn)
                    st.success(f"Insumo '{nombre_nuevo}' agregado (ID {nuevo_id}).")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

insumos = db.list_insumos(conn)

if not insumos:
    st.warning("No hay insumos cargados en el catálogo.")
    st.stop()

hoy = date.today()
filas = []
for i in insumos:
    d = dict(i)
    alertas = calcular_alertas(d["stock_actual"], d["stock_minimo"], d["frecuencia_uso_mensual"], hoy)
    d.update(alertas)
    d["alerta_icono"] = "🔴" if alertas["alerta_nivel"] == "REPONER AHORA" else ("🟢" if alertas["alerta_nivel"] == "OK" else "⚪")
    d["ventana_icono"] = (
        "🟠" if alertas["alerta_ventana"] == "FUERA DE VENTANA"
        else ("🟢" if alertas["alerta_ventana"] == "DENTRO DE VENTANA" else "")
    )
    filas.append(d)

df = pd.DataFrame(filas)

st.caption(
    "🔴 stock actual ≤ stock mínimo (reponer ahora) · 🟢 OK. "
    "Ventana de compra: 🟠 el stock proyecta caer al mínimo después del día 20 (fuera de la ventana de "
    "facturación SDT-USACH) · 🟢 dentro de ventana. Ordenado por clase ABC (A primero). "
    "Edita las celdas habilitadas y presiona **Guardar cambios**; el stock mínimo y la clasificación ABC "
    "se recalculan solos para todo el catálogo."
)

columnas_orden = [
    "alerta_icono", "id", "codigo", "nombre", "categoria", "operacion", "clase_abc",
    "stock_actual", "stock_minimo", "ventana_icono", "dia_proyectado",
    "unidad", "ubicacion", "proveedor",
    "costo_unitario", "unidades_por_cambio", "frecuencia_uso_mensual", "rendimiento_probetas",
    "impacto_operacional", "tiempo_reposicion_dias", "fuente_dato",
]
df = df[columnas_orden]

if st.button("🏷️ Generar códigos automáticos para insumos sin código"):
    asignados = db.asignar_codigos_automaticos(conn)
    st.success(f"{asignados} insumo(s) recibieron un código nuevo (formato INS0000).")
    st.rerun()

editado = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    disabled=["alerta_icono", "id", "clase_abc", "stock_actual", "stock_minimo",
              "ventana_icono", "dia_proyectado", "nombre"],
    column_config={
        "alerta_icono": st.column_config.TextColumn("⚠"),
        "id": st.column_config.NumberColumn("ID"),
        "codigo": st.column_config.TextColumn("Código"),
        "nombre": st.column_config.TextColumn("Insumo"),
        "categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS),
        "operacion": st.column_config.TextColumn("Operación"),
        "clase_abc": st.column_config.TextColumn("Clase ABC"),
        "stock_actual": st.column_config.NumberColumn("Stock actual", format="%.2f"),
        "stock_minimo": st.column_config.NumberColumn("Stock mínimo", format="%.2f", help="Calculado automáticamente."),
        "ventana_icono": st.column_config.TextColumn("Ventana compra"),
        "dia_proyectado": st.column_config.NumberColumn("Día proyectado agotamiento"),
        "unidad": st.column_config.TextColumn("Unidad"),
        "ubicacion": st.column_config.TextColumn("Ubicación"),
        "proveedor": st.column_config.TextColumn("Proveedor"),
        "costo_unitario": st.column_config.NumberColumn("Costo unitario (CLP)", format="%.2f"),
        "unidades_por_cambio": st.column_config.NumberColumn("N° unid. por cambio", format="%.0f"),
        "frecuencia_uso_mensual": st.column_config.NumberColumn("Frecuencia uso mensual", format="%.2f"),
        "rendimiento_probetas": st.column_config.NumberColumn("Rendimiento (probetas/cambio)", format="%.2f"),
        "impacto_operacional": st.column_config.NumberColumn("Impacto operacional (1-5)", min_value=1, max_value=5, step=1),
        "tiempo_reposicion_dias": st.column_config.NumberColumn("Tiempo reposición (días)", format="%.2f"),
        "fuente_dato": st.column_config.TextColumn("Fuente del dato (rendimiento)"),
    },
    key="editor_insumos",
)

if st.button("💾 Guardar cambios", type="primary"):
    campos_editables = [
        "categoria", "operacion", "unidad", "ubicacion", "proveedor",
        "costo_unitario", "unidades_por_cambio", "frecuencia_uso_mensual", "rendimiento_probetas",
        "impacto_operacional", "tiempo_reposicion_dias", "fuente_dato",
    ]
    original_por_id = {row["id"]: row for row in df.to_dict("records")}
    cambios = 0
    errores = []
    for _, row in editado.iterrows():
        insumo_id = int(row["id"])
        original = original_por_id.get(insumo_id, {})

        if row["codigo"] != original.get("codigo"):
            try:
                db.set_codigo(conn, insumo_id, None if pd.isna(row["codigo"]) else row["codigo"])
                cambios += 1
            except ValueError as e:
                errores.append(str(e))

        diferencias = {c: row[c] for c in campos_editables if row[c] != original.get(c)}
        if diferencias:
            diferencias = {k: (None if pd.isna(v) else v) for k, v in diferencias.items()}
            db.update_insumo_campos(conn, insumo_id, **diferencias)
            cambios += 1

    recalcular_catalogo(conn)

    if errores:
        st.error(" / ".join(errores))
    st.success(f"{cambios} cambio(s) guardado(s). Clasificación ABC y stock mínimo recalculados.")
    st.rerun()

st.divider()
st.subheader("⬇ Exportar")

insumos_export = db.list_insumos(conn)
filas_export = []
for i in insumos_export:
    d = dict(i)
    alertas = calcular_alertas(d["stock_actual"], d["stock_minimo"], d["frecuencia_uso_mensual"], hoy)
    d.update(alertas)
    filas_export.append(d)

export_df = pd.DataFrame(filas_export)
export_df = export_df.rename(columns={
    "id": "ID", "codigo": "Código", "nombre": "Nombre del ítem", "categoria": "Categoría",
    "operacion": "Operación", "costo_unitario": "Costo unitario (CLP)",
    "unidades_por_cambio": "N° unidades por cambio", "frecuencia_uso_mensual": "Frecuencia de uso (mensual)",
    "rendimiento_probetas": "Rendimiento (probetas/cambio)",
    "impacto_operacional": "Impacto operacional (1-5)", "tiempo_reposicion_dias": "Tiempo de reposición (días)",
    "puntaje_ponderado": "Puntaje ponderado", "clase_abc": "Clasificación ABC",
    "stock_actual": "Stock actual", "stock_minimo": "Stock mínimo",
    "unidad": "Unidad", "ubicacion": "Ubicación", "proveedor": "Proveedor",
    "fuente_dato": "Fuente del dato", "alerta_nivel": "Alerta nivel de stock",
    "fecha_proyectada": "Fecha proyectada stock mínimo", "dia_proyectado": "Día proyectado",
    "alerta_ventana": "Alerta ventana de compra",
})
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    export_df.to_excel(writer, index=False, sheet_name="Estado de insumos")

st.download_button(
    "Exportar a Excel",
    data=buffer.getvalue(),
    file_name="estado_insumos_simet.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()
st.subheader("🏷️ Etiquetas para imprimir")
st.caption(
    "Genera un PDF con etiquetas de código de barras (una por insumo con código asignado), "
    "listas para imprimir y pegar en cada insumo. Se leen con cualquier lector de código de barras USB."
)
insumos_con_codigo = [i for i in insumos_export if i["codigo"]]
st.caption(f"{len(insumos_con_codigo)} de {len(insumos_export)} insumos tienen código asignado.")
if insumos_con_codigo:
    pdf_bytes = generar_pdf_etiquetas(insumos_con_codigo)
    st.download_button(
        "Descargar etiquetas (PDF)",
        data=pdf_bytes,
        file_name="etiquetas_insumos_simet.pdf",
        mime="application/pdf",
    )
else:
    st.caption("Ningún insumo tiene código todavía — usa el botón de arriba para generarlos automáticamente.")

conn.close()
