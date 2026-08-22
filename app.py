import streamlit as st

import db
import seed_from_excel

st.set_page_config(page_title="Control de Insumos Críticos — SIMET-USACH", page_icon="🧪", layout="wide")

if not db.db_exists():
    with st.spinner("Cargando datos iniciales desde los Excel de la tesis..."):
        n_insumos, n_consumo = seed_from_excel.seed()
    st.toast(f"Base de datos creada: {n_insumos} insumos, {n_consumo} filas de consumo por operación.")

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
col3.metric("Bajo stock mínimo", sum(1 for i in insumos if i["stock_actual"] < i["stock_minimo"]))
conn.close()
