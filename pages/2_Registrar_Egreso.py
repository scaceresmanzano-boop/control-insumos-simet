from datetime import date

import streamlit as st

import db
from scan_ui import selector_con_scanner

st.set_page_config(page_title="Registrar egreso", page_icon="📤", layout="wide")
st.title("📤 Registrar egreso de insumo")

conn = db.get_connection()
insumos = db.list_insumos(conn)

if not insumos:
    st.warning("No hay insumos cargados en el catálogo.")
    st.stop()

opciones, opciones_list, default_index, preseleccion_key = selector_con_scanner(insumos, "egreso")

with st.form("form_egreso", clear_on_submit=True):
    seleccion = st.selectbox("Insumo", options=opciones_list, index=default_index)
    cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0, format="%g")
    ensayo_ot = st.text_input("Ensayo / OT asociado")
    responsable = st.text_input("Responsable")
    fecha = st.date_input("Fecha", value=date.today())
    observacion = st.text_area("Observación (opcional)", "")
    enviado = st.form_submit_button("Registrar egreso")

    if enviado:
        insumo_id = opciones[seleccion]
        if cantidad <= 0:
            st.error("La cantidad debe ser mayor a 0.")
        elif not ensayo_ot.strip():
            st.error("Debes indicar el ensayo/OT asociado.")
        elif not responsable.strip():
            st.error("Debes indicar el responsable.")
        else:
            try:
                db.registrar_egreso(
                    conn, insumo_id, cantidad, ensayo_ot.strip(), responsable.strip(),
                    fecha.isoformat(), observacion or None,
                )
                st.session_state[preseleccion_key] = None
                st.success(f"Egreso registrado: -{cantidad:g} de '{seleccion.split(' (stock')[0]}'.")
            except ValueError as e:
                st.error(str(e))

st.subheader("Últimos egresos registrados")
movimientos = [m for m in db.list_movimientos(conn, limit=50) if m["tipo"] == "egreso"]
if movimientos:
    st.dataframe(
        [
            {
                "Fecha": m["fecha"],
                "Insumo": m["insumo_nombre"],
                "Cantidad": m["cantidad"],
                "Ensayo/OT": m["ensayo_ot"],
                "Responsable": m["responsable"],
                "Observación": m["observacion"],
            }
            for m in movimientos
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("Aún no hay egresos registrados.")

conn.close()
