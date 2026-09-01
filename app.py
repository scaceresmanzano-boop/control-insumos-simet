from datetime import date

import streamlit as st

import db
from bootstrap import asegurar_base_lista
from theme import aplicar_tema, hero_banner, stat_card

st.set_page_config(page_title="Control de Insumos Críticos — SIMET-USACH", page_icon="🧪", layout="wide")
aplicar_tema()

with st.spinner("Preparando la base de datos..."):
    asegurar_base_lista()

conn = db.get_connection()
insumos = db.list_insumos(conn)
n_clase_a = sum(1 for i in insumos if i["clase_abc"] == "A")
n_reponer = sum(1 for i in insumos if i["stock_minimo"] is not None and i["stock_actual"] <= i["stock_minimo"])
conn.close()

hero_banner(
    "🧪 Control de Insumos Críticos",
    "Laboratorio SIMET-USACH",
    pills=[f"Hoy: {date.today().strftime('%d-%m-%Y')}", f"{len(insumos)} insumos catastrados"],
)

st.markdown("Usa el menú de la izquierda para navegar entre las pantallas.")

col1, col2, col3 = st.columns(3)
with col1:
    stat_card("📦", "Insumos en catálogo", len(insumos))
with col2:
    stat_card("🅰️", "Clase A", n_clase_a)
with col3:
    stat_card("🔴", "A reponer ahora", n_reponer, value_color="#C0392B" if n_reponer else None)

st.divider()

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("**📥 Registrar ingreso**")
    st.caption("Suma stock de un insumo (compra recibida).")
with col_b:
    st.markdown("**📤 Registrar egreso**")
    st.caption("Descuenta stock al consumir un insumo en un ensayo/OT.")
with col_c:
    st.markdown("**📊 Ver estado**")
    st.caption("Catálogo completo ordenado por clase ABC, con alertas.")
