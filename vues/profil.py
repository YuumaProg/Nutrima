from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from nutrima import auth, db, ui
from nutrima.referentiels import OBJECTIFS, SEXES

u = ui.uid()
p = ui.profil(date.today())
nouveau = p is None

st.title("👤 Mon profil")
if nouveau:
    st.info("Bienvenue ! Remplis ton profil pour obtenir des repères adaptés à ton âge et à ta corpulence.")

aujourdhui = date.today()
with st.form("profil"):
    c1, c2 = st.columns(2)
    prenom = c1.text_input("Prénom (facultatif)", p.prenom if p else "", max_chars=40)
    naissance = c2.date_input(
        "Date de naissance", p.naissance if p else date(aujourdhui.year - 30, 1, 1),
        min_value=date(1920, 1, 1), max_value=aujourdhui - timedelta(days=5 * 365), format="DD/MM/YYYY")
    c1, c2, c3 = st.columns(3)
    sexe = c1.radio("Sexe", SEXES, index=SEXES.index(p.sexe) if p else 0, horizontal=True,
                    help="Utilisé uniquement pour estimer le métabolisme de base.")
    taille = c2.number_input("Taille (cm)", 100, 220, int(p.taille) if p else 170)
    poids = c3.number_input("Poids actuel (kg)", 15.0, 250.0, float(p.poids) if p else 70.0, 0.5)
    objectifs = list(OBJECTIFS)
    objectif = st.selectbox("Objectif", objectifs, index=objectifs.index(p.objectif) if p else 0,
                            help="Pour les moins de 18 ans, l'objectif reste « maintenir » quel que soit le choix.")
    if st.form_submit_button("💾 Enregistrer", type="primary"):
        db.enregistrer_profil(u, prenom, naissance, sexe, taille, objectif)
        if p is None or abs(poids - p.poids) > 1e-9:
            db.enregistrer_poids(u, aujourdhui, poids)
        st.success("Profil enregistré.")
        st.rerun()

if nouveau:
    st.stop()

# ---------------------------------------------------------------------------
st.subheader("⚖️ Suivi du poids")
c1, c2, c3 = st.columns([1.2, 1, 1])
d_poids = c1.date_input("Date de la pesée", aujourdhui, max_value=aujourdhui, format="DD/MM/YYYY", key="d_poids")
kg = c2.number_input("Poids (kg)", 15.0, 250.0, float(p.poids), 0.1, key="kg")
c3.write("")
if c3.button("Ajouter la pesée", width="stretch"):
    db.enregistrer_poids(u, d_poids, kg)
    st.rerun()
hist = db.historique_poids(u)
if len(hist) > 1:
    st.altair_chart(
        alt.Chart(hist.assign(date=pd.to_datetime(hist["date"]))).mark_line(point=True).encode(
            alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m/%y")),
            alt.Y("kg:Q", title="kg", scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), "kg:Q"]).properties(height=220),
        width="stretch")
with st.expander(f"Historique ({len(hist)} pesée(s))"):
    st.dataframe(hist.sort_values("date", ascending=False).rename(columns={"date": "Date", "kg": "Poids (kg)"}),
                 hide_index=True, width="stretch")
    if len(hist) > 1:
        a_suppr = st.selectbox("Supprimer une pesée", hist["date"], format_func=lambda d: d.strftime("%d/%m/%Y"))
        if st.button("Supprimer cette pesée"):
            db.supprimer_poids(u, a_suppr)
            st.rerun()

# ---------------------------------------------------------------------------
st.subheader("📦 Mes données")
c1, c2, c3 = st.columns(3)
c1.download_button("⬇️ Activités (CSV)", db.activites(u).drop(columns=["id", "tag"]).to_csv(index=False).encode("utf-8-sig"),
                   "nutrima_activites.csv", "text/csv", width="stretch")
c2.download_button("⬇️ Alimentation (CSV)", db.aliments(u).drop(columns=["id"]).to_csv(index=False).encode("utf-8-sig"),
                   "nutrima_alimentation.csv", "text/csv", width="stretch")
c3.download_button("⬇️ Poids (CSV)", hist.to_csv(index=False).encode("utf-8-sig"),
                   "nutrima_poids.csv", "text/csv", width="stretch")

with st.expander("🔑 Changer de mot de passe"):
    with st.form("mdp", clear_on_submit=True):
        ancien = st.text_input("Mot de passe actuel", type="password")
        n1 = st.text_input("Nouveau mot de passe", type="password")
        n2 = st.text_input("Confirme le nouveau mot de passe", type="password")
        if st.form_submit_button("Changer"):
            try:
                auth.changer_mdp(u, st.session_state.username, ancien, n1, n2)
                st.success("Mot de passe modifié.")
            except auth.ErreurAuth as e:
                st.error(str(e))

with st.expander("⚠️ Zone de danger"):
    st.markdown("**Effacer mon suivi** : supprime toutes les activités, repas et temps assis (le profil et le poids sont conservés).")
    if st.checkbox("Je confirme vouloir effacer mon suivi", key="conf_effacer"):
        if st.button("Effacer mon suivi", type="primary"):
            db.effacer_donnees(u)
            st.success("Suivi effacé.")
    st.divider()
    st.markdown("**Supprimer mon compte** : supprime définitivement le compte et toutes ses données.")
    with st.form("suppr_compte"):
        mdp = st.text_input("Mot de passe pour confirmer", type="password")
        if st.form_submit_button("Supprimer définitivement mon compte"):
            try:
                auth.connecter(st.session_state.username, mdp)
                db.supprimer_utilisateur(u)
                ui.deconnecter()
                st.rerun()
            except auth.ErreurAuth:
                st.error("Mot de passe incorrect.")
