"""Gate simple de contraseña (via st.secrets) para funciones restringidas a admin."""
import streamlit as st

SESSION_KEY = "es_admin"


def requiere_admin(etiqueta):
    """Devuelve True si ya se autenticó como admin en esta sesión de navegador.
    Si no, muestra un campo de contraseña (y devuelve False) hasta que se ingrese bien."""
    if st.session_state.get(SESSION_KEY):
        return True

    admin_password = st.secrets.get("admin_password")
    if not admin_password:
        st.warning(
            "Esta función requiere una contraseña de administrador que todavía no está "
            'configurada. Agrega `admin_password = "..."` en `.streamlit/secrets.toml` '
            "(local) o en Settings → Secrets (Streamlit Cloud)."
        )
        return False

    with st.form(f"form_auth_{etiqueta}", clear_on_submit=True):
        clave = st.text_input(f"🔒 Contraseña para {etiqueta}", type="password")
        if st.form_submit_button("Desbloquear"):
            if clave == admin_password:
                st.session_state[SESSION_KEY] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    return False
