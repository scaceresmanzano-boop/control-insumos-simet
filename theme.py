"""Estilo visual compartido de la app — tarjetas redondeadas, paleta verde
azulado, badges tipo píldora, inspirado en apps móviles de gestión (RR.HH.
estilo Buk). Se aplica inyectando CSS; los colores base también están en
.streamlit/config.toml (theme)."""
import streamlit as st

VERDE = "#0F6D5C"
VERDE_CLARO = "#EAF4F1"
ROJO = "#C0392B"
AMBAR = "#B7791F"
GRIS_TEXTO = "#6B7280"

_CSS = f"""
<style>
/* Fondo general suave, como el gris claro de la app de referencia */
[data-testid="stAppViewContainer"] > .main {{
    background-color: #F4F7F6;
}}

/* Tarjetas de estadística (stat-card) */
.stat-card {{
    background: #FFFFFF;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(15, 109, 92, 0.12);
    border: 1px solid #E7EEEC;
    height: 100%;
}}
.stat-card .stat-icon {{
    font-size: 1.4rem;
    margin-bottom: 6px;
}}
.stat-card .stat-label {{
    color: {GRIS_TEXTO};
    font-size: 0.85rem;
    margin-bottom: 2px;
}}
.stat-card .stat-value {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
}}

/* Banner superior tipo tarjeta de perfil (degradado verde azulado) */
.hero-banner {{
    background: linear-gradient(135deg, {VERDE} 0%, #14877A 100%);
    border-radius: 20px;
    padding: 28px 26px;
    margin-bottom: 22px;
    color: white;
}}
.hero-banner h1 {{
    color: white !important;
    font-size: 1.6rem;
    margin: 0 0 6px 0;
}}
.hero-banner p {{
    color: rgba(255,255,255,0.9);
    margin: 0;
    font-size: 0.95rem;
}}
.hero-pill {{
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 0.82rem;
    margin-top: 12px;
    margin-right: 8px;
}}

/* Botones primarios redondeados */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
    border-radius: 12px;
    font-weight: 600;
    padding: 0.55rem 1rem;
}}

/* Botón de ingreso en verde, botón de egreso en rojo (por key) */
.st-key-ingreso_submit button {{
    background-color: {VERDE} !important;
    border-color: {VERDE} !important;
    color: white !important;
}}
.st-key-egreso_submit button {{
    background-color: {ROJO} !important;
    border-color: {ROJO} !important;
    color: white !important;
}}

/* Expanders y contenedores con esquinas más redondeadas */
[data-testid="stExpander"] {{
    border-radius: 16px !important;
    border: 1px solid #E7EEEC !important;
    overflow: hidden;
}}

/* Sidebar con acento verde suave */
[data-testid="stSidebar"] {{
    background-color: {VERDE_CLARO};
}}
</style>
"""


def aplicar_tema():
    st.markdown(_CSS, unsafe_allow_html=True)


def hero_banner(titulo, subtitulo, pills=None):
    pills_html = "".join(f'<span class="hero-pill">{p}</span>' for p in (pills or []))
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
            {pills_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(icon, label, value, value_color=None):
    color_style = f"color:{value_color};" if value_color else ""
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-icon">{icon}</div>
            <div class="stat-label">{label}</div>
            <div class="stat-value" style="{color_style}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
