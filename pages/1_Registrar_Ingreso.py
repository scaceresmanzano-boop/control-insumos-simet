from datetime import date

import streamlit as st

import db
from bootstrap import asegurar_base_lista
from scan_ui import selector_con_scanner

st.set_page_config(page_title="Registrar ingreso", page_icon="📥", layout="wide")
st.title("📥 Registrar ingreso de insumo")

asegurar_base_lista()
conn = db.get_connection()
insumos = db.list_insumos(conn)

if not insumos:
    st.warning("No hay insumos cargados en el catálogo.")
    st.stop()

opciones, opciones_list, default_index, preseleccion_key = selector_con_scanner(insumos, "ingreso")

with st.form("form_ingreso", clear_on_submit=True):
    seleccion = st.selectbox("Insumo", options=opciones_list, index=default_index)
    cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0, format="%g")
    proveedor = st.text_input("Proveedor")
    fecha = st.date_input("Fecha", value=date.today())
    observacion = st.text_area("Observación (opcional)", "")
    enviado = st.form_submit_button("Registrar ingreso")

    if enviado:
        if cantidad <= 0:
            st.error("La cantidad debe ser mayor a 0.")
        else:
            insumo_id = opciones[seleccion]
            db.registrar_ingreso(
                conn, insumo_id, cantidad, proveedor or None, fecha.isoformat(), observacion or None
            )
            st.session_state[preseleccion_key] = None
            st.success(f"Ingreso registrado: +{cantidad:g} de '{seleccion.split(' (stock')[0]}'.")

st.subheader("Últimos ingresos registrados")
movimientos = [m for m in db.list_movimientos(conn, limit=50) if m["tipo"] == "ingreso"]
if movimientos:
    st.dataframe(
        [
            {
                "Fecha": m["fecha"],
                "Insumo": m["insumo_nombre"],
                "Cantidad": m["cantidad"],
                "Proveedor": m["proveedor"],
                "Observación": m["observacion"],
            }
            for m in movimientos
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("Aún no hay ingresos registrados.")

conn.close()
