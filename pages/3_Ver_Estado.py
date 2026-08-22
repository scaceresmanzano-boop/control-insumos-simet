from io import BytesIO

import pandas as pd
import streamlit as st

import db
from abc_scoring import calcular_clasificacion_abc
from db import CATEGORIAS

st.set_page_config(page_title="Ver estado", page_icon="📊", layout="wide")
st.title("📊 Estado de insumos")

conn = db.get_connection()
insumos = db.list_insumos(conn)

if not insumos:
    st.warning("No hay insumos cargados en el catálogo.")
    st.stop()


def alerta(row):
    if row["stock_actual"] < row["stock_minimo"]:
        return "🔴"
    if row["stock_minimo"] > 0 and row["stock_actual"] <= row["stock_minimo"] * 1.2:
        return "🟠"
    return "🟢"


df = pd.DataFrame([dict(i) for i in insumos])
df["alerta"] = df.apply(alerta, axis=1)

st.caption(
    "🔴 stock bajo el mínimo · 🟠 stock dentro de un 20% sobre el mínimo · 🟢 stock saludable. "
    "Edita las celdas habilitadas y presiona **Guardar cambios** para actualizar; los criterios "
    "ABC (costo, frecuencia, impacto, tiempo de reposición) se recalculan para todo el catálogo al guardar."
)

columnas_orden = [
    "alerta", "id", "nombre", "categoria", "clase_abc", "puntaje_ponderado",
    "stock_actual", "stock_minimo", "unidad", "proveedor",
    "costo_unitario", "frecuencia_uso_mensual", "impacto_operacional", "tiempo_reposicion_dias",
]
df = df[columnas_orden]

editado = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    disabled=["alerta", "id", "clase_abc", "puntaje_ponderado", "nombre"],
    column_config={
        "alerta": st.column_config.TextColumn("⚠"),
        "id": st.column_config.NumberColumn("ID"),
        "nombre": st.column_config.TextColumn("Insumo"),
        "categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS),
        "clase_abc": st.column_config.TextColumn("Clase ABC"),
        "puntaje_ponderado": st.column_config.NumberColumn("Puntaje", format="%.4f"),
        "stock_actual": st.column_config.NumberColumn("Stock actual", format="%.2f"),
        "stock_minimo": st.column_config.NumberColumn("Stock mínimo", format="%.2f"),
        "unidad": st.column_config.TextColumn("Unidad"),
        "proveedor": st.column_config.TextColumn("Proveedor"),
        "costo_unitario": st.column_config.NumberColumn("Costo unitario (CLP)", format="%.2f"),
        "frecuencia_uso_mensual": st.column_config.NumberColumn("Frecuencia uso mensual", format="%.2f"),
        "impacto_operacional": st.column_config.NumberColumn("Impacto operacional (1-5)", min_value=1, max_value=5, step=1),
        "tiempo_reposicion_dias": st.column_config.NumberColumn("Tiempo reposición (días)", format="%.2f"),
    },
    key="editor_insumos",
)

if st.button("💾 Guardar cambios", type="primary"):
    campos_editables = [
        "categoria", "stock_minimo", "unidad", "proveedor",
        "costo_unitario", "frecuencia_uso_mensual", "impacto_operacional", "tiempo_reposicion_dias",
    ]
    original_por_id = {row["id"]: row for row in df.to_dict("records")}
    cambios = 0
    for _, row in editado.iterrows():
        original = original_por_id.get(row["id"], {})
        diferencias = {c: row[c] for c in campos_editables if row[c] != original.get(c)}
        if diferencias:
            diferencias = {k: (None if pd.isna(v) else v) for k, v in diferencias.items()}
            db.update_insumo_campos(conn, int(row["id"]), **diferencias)
            cambios += 1

    resultados = calcular_clasificacion_abc(db.list_insumos(conn))
    db.update_scores_masivo(conn, resultados)

    st.success(f"{cambios} insumo(s) actualizado(s). Clasificación ABC recalculada.")
    st.rerun()

st.divider()
st.subheader("⬇ Exportar")

export_df = pd.DataFrame([dict(i) for i in db.list_insumos(conn)])
export_df = export_df.rename(columns={
    "id": "ID", "nombre": "Nombre del ítem", "categoria": "Categoría",
    "costo_unitario": "Costo unitario (CLP)", "frecuencia_uso_mensual": "Frecuencia de uso (mensual)",
    "impacto_operacional": "Impacto operacional (1-5)", "tiempo_reposicion_dias": "Tiempo de reposición (días)",
    "puntaje_ponderado": "Puntaje ponderado", "clase_abc": "Clasificación ABC",
    "stock_actual": "Stock actual", "stock_minimo": "Stock mínimo",
    "unidad": "Unidad", "proveedor": "Proveedor",
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
st.subheader("📎 Referencia: consumo por operación")
st.caption("Datos de la ficha de consumo por operación (rendimiento por probeta). No afecta el stock.")
consumo = db.list_consumo_operaciones(conn)
if consumo:
    st.dataframe([dict(c) for c in consumo], use_container_width=True, hide_index=True)
else:
    st.caption("Sin datos de consumo por operación cargados.")

conn.close()
