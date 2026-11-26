"""
Nutrima : lutter contre la sédentarité et mieux manger, à tout âge (ODD 3 : bonne santé et bien-être).
Lancement : streamlit run app.py
"""
import streamlit as st

from nutrima import ui

st.set_page_config(page_title="Nutrima", page_icon="🥗", layout="wide")
ui.initialiser_base()

a_propos = st.Page("vues/a_propos.py", title="ODD 3 & à propos", icon=":material/public:")

if ui.uid() is None:
    pg = st.navigation([st.Page(ui.page_connexion, title="Connexion", icon=":material/login:"), a_propos])
    pg.run()
    st.stop()

p = ui.profil()
profil_page = st.Page("vues/profil.py", title="Mon profil", icon=":material/person:", default=p is None)

if p is None:
    # Tant que le profil n'est pas rempli, seule la page profil est accessible
    pages = [profil_page, a_propos]
else:
    pages = {
        "Mon suivi": [
            st.Page("vues/aujourdhui.py", title="Aujourd'hui", icon=":material/today:", default=True),
            st.Page("vues/activite.py", title="Activité", icon=":material/directions_run:"),
            st.Page("vues/alimentation.py", title="Alimentation", icon=":material/restaurant:"),
            st.Page("vues/tendances.py", title="Tendances", icon=":material/monitoring:"),
        ],
        "Compte": [profil_page, a_propos],
    }

pg = st.navigation(pages)
ui.barre_laterale(p)
pg.run()
