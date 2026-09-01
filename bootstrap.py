"""Garantiza que la base de datos exista, tenga el esquema al día (migra
columnas nuevas a una base ya existente) y, si es la primera vez, esté
sembrada y con la clasificación ABC / stock mínimo ya calculados.

Se llama al inicio de app.py y de cada página — así funciona sin importar
por cuál pantalla entre la persona primero."""
import streamlit as st

import db
import seed_from_excel
from recalculo import recalcular_catalogo


@st.cache_resource
def asegurar_base_lista():
    es_nueva = not db.db_exists()
    conn = db.get_connection()
    db.init_schema(conn)  # CREATE TABLE IF NOT EXISTS + ALTER TABLE para bases ya existentes
    conn.close()

    if es_nueva:
        seed_from_excel.seed()
        conn = db.get_connection()
        recalcular_catalogo(conn)
        conn.close()
    return True
