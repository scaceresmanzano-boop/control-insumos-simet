"""Widget reutilizable: campo de escaneo de código de barras + selector de insumo.

Un lector de código de barras USB funciona como un teclado: al escanear escribe
el código y presiona Enter, lo que dispara on_change en un st.text_input normal.
"""
import streamlit as st

import db


def selector_con_scanner(insumos, key_prefix):
    opciones = {f"{i['nombre']} (stock actual: {i['stock_actual']:g})": i["id"] for i in insumos}
    opciones_list = list(opciones.keys())
    id_a_opcion = {v: k for k, v in opciones.items()}

    preseleccion_key = f"{key_prefix}_preseleccion"
    scan_key = f"{key_prefix}_scan"
    msg_key = f"{key_prefix}_scan_msg"

    if preseleccion_key not in st.session_state:
        st.session_state[preseleccion_key] = None

    def _on_scan():
        codigo = st.session_state.get(scan_key, "")
        conn_local = db.get_connection()
        insumo = db.get_insumo_por_codigo(conn_local, codigo)
        conn_local.close()
        if insumo:
            st.session_state[preseleccion_key] = insumo["id"]
            st.session_state[msg_key] = ("success", f"✅ {insumo['nombre']} (stock actual: {insumo['stock_actual']:g})")
        elif codigo.strip():
            st.session_state[msg_key] = ("error", f"⚠️ Código '{codigo}' no encontrado en el catálogo.")
        st.session_state[scan_key] = ""

    st.text_input(
        "📷 Escanear código de barras (opcional)",
        key=scan_key,
        on_change=_on_scan,
        placeholder="Haz clic aquí y escanea con el lector USB...",
    )
    if st.session_state.get(msg_key):
        nivel, texto = st.session_state[msg_key]
        (st.success if nivel == "success" else st.error)(texto)

    default_index = 0
    preseleccion_id = st.session_state.get(preseleccion_key)
    if preseleccion_id is not None:
        nombre_opcion = id_a_opcion.get(preseleccion_id)
        if nombre_opcion in opciones_list:
            default_index = opciones_list.index(nombre_opcion)

    return opciones, opciones_list, default_index, preseleccion_key
