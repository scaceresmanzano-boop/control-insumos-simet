from datetime import date

import streamlit as st

import db
from db import OTRO_USUARIO
from scan_ui import selector_con_scanner

st.set_page_config(page_title="Registrar egreso", page_icon="📤", layout="wide")
st.title("📤 Registrar egreso de insumo")

conn = db.get_connection()
insumos = db.list_insumos(conn)

if not insumos:
    st.warning("No hay insumos cargados en el catálogo.")
    st.stop()

opciones, opciones_list, default_index, preseleccion_key = selector_con_scanner(insumos, "egreso")

seleccion = st.selectbox("Insumo", options=opciones_list, index=default_index, key="egreso_insumo_select")
insumo_id = opciones[seleccion]

ultimo = db.get_ultimo_egreso(conn, insumo_id)
if ultimo:
    st.caption(
        f"📋 Último retiro: **{ultimo['cantidad']:g}** el {ultimo['fecha']} por "
        f"**{ultimo['responsable']}** (Ensayo/OT: {ultimo['ensayo_ot'] or '—'})."
    )
else:
    st.caption("📋 Sin retiros previos registrados para este insumo.")

usuarios = db.list_usuarios(conn)

with st.form("form_egreso", clear_on_submit=True):
    cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0, format="%g")
    ensayo_ot = st.text_input("Ensayo / OT asociado")
    responsable_sel = st.selectbox("Responsable", options=usuarios + [OTRO_USUARIO])
    responsable_nuevo = st.text_input("Si elegiste 'Otro (nuevo)', escribe las iniciales o nombre aquí")
    fecha = st.date_input("Fecha", value=date.today())
    observacion = st.text_area("Observación (opcional)", "")
    enviado = st.form_submit_button("Registrar egreso")

    if enviado:
        responsable = responsable_nuevo.strip() if responsable_sel == OTRO_USUARIO else responsable_sel
        if cantidad <= 0:
            st.error("La cantidad debe ser mayor a 0.")
        elif not ensayo_ot.strip():
            st.error("Debes indicar el ensayo/OT asociado.")
        elif not responsable:
            st.error("Debes indicar el responsable (o escribir uno nuevo si elegiste 'Otro').")
        else:
            try:
                db.registrar_egreso(
                    conn, insumo_id, cantidad, ensayo_ot.strip(), responsable,
                    fecha.isoformat(), observacion or None,
                )
                if responsable_sel == OTRO_USUARIO:
                    db.crear_usuario(conn, responsable)
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
