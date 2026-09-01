import streamlit as st

import db
from bootstrap import asegurar_base_lista

st.set_page_config(page_title="Control de Insumos Críticos — SIMET-USACH", page_icon="🧪", layout="wide")

with st.spinner("Preparando la base de datos..."):
    asegurar_base_lista()

st.title("🧪 Control de Insumos Críticos — SIMET-USACH")
st.markdown(
    """
Usa el menú de la izquierda para navegar entre las pantallas:

- **Registrar ingreso** — suma stock de un insumo (compra recibida).
- **Registrar egreso** — descuenta stock al consumir un insumo en un ensayo/OT.
- **Ver estado** — catálogo completo ordenado por clase ABC, con alertas de stock bajo mínimo.
"""
)

conn = db.get_connection()
insumos = db.list_insumos(conn)
col1, col2, col3 = st.columns(3)
col1.metric("Insumos en catálogo", len(insumos))
col2.metric("Clase A", sum(1 for i in insumos if i["clase_abc"] == "A"))
col3.metric(
    "A reponer ahora",
    sum(1 for i in insumos if i["stock_minimo"] is not None and i["stock_actual"] <= i["stock_minimo"]),
)
conn.close()
