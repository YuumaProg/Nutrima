import streamlit as st

from nutrima import db, ui
from nutrima.calculs import nouvelle_activite
from nutrima.referentiels import ACTIVITES

u, j = ui.uid(), ui.jour()
p = ui.profil(j)

st.title(f"🏃 Activité du {j.strftime('%d/%m/%Y')}")

with st.form("f_act", clear_on_submit=True):
    c1, c2 = st.columns([2, 1])
    act = c1.selectbox("Activité", list(ACTIVITES))
    duree = c2.number_input("Durée (min)", 5, 600, 30, 5)
    if st.form_submit_button("➕ Ajouter l'activité", type="primary"):
        db.ajouter_activite(u, j, nouvelle_activite(act, duree, p.poids))
        st.toast(f"{act} ajoutée ({duree} min).", icon="✅")

a = db.activites(u, j, j)
if a.empty:
    st.caption("Aucune activité saisie pour ce jour.")
else:
    vue = a[["nom", "duree", "intensite", "kcal"]].rename(columns={
        "nom": "Activité", "duree": "Durée (min)", "intensite": "Intensité", "kcal": "Dépense (kcal)"})
    ev = st.dataframe(vue, hide_index=True, width="stretch", on_select="rerun",
                      selection_mode="multi-row", key=f"tab_act_{st.session_state.get('v_act', 0)}")
    c1, c2 = st.columns([3, 1])
    c1.caption(f"Total : {int(a['duree'].sum())} min, {int(a['kcal'].sum())} kcal dépensées en plus du repos. "
               "Sélectionne des lignes pour les supprimer.")
    sel = ev.selection.rows
    if c2.button(f"🗑️ Supprimer ({len(sel)})", disabled=not sel, width="stretch"):
        db.supprimer_lignes("activites", u, a.iloc[sel]["id"].tolist())
        st.session_state.v_act = st.session_state.get("v_act", 0) + 1  # réinitialise la sélection
        st.rerun()

st.divider()
st.subheader("🪑 Temps assis ou devant un écran")
st.caption("Travail, repas, écrans, transports : compte toutes les heures passées assis ce jour-là.")
deja = db.assis(u, j, j).get(j)
c1, c2, c3 = st.columns([2, 1, 1])
h = c1.slider("Heures assis", 0.0, 18.0, deja if deja is not None else 6.0, 0.5, key=f"assis_{j}")
c2.write("")
if c2.button("💾 Enregistrer", width="stretch", type="primary" if deja is None else "secondary"):
    db.enregistrer_assis(u, j, h)
    st.rerun()
c3.write("")
if c3.button("Effacer", width="stretch", disabled=deja is None):
    db.enregistrer_assis(u, j, None)
    st.rerun()
if deja is None:
    st.info("Temps assis non renseigné pour ce jour : il n'est pas compté dans le score.")
else:
    st.success(f"Temps assis enregistré : {deja:g} h.")
