"""Aides d'interface partagées par les pages Streamlit."""
from __future__ import annotations

import time
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from . import auth, db
from .calculs import Profil, bilan

TENTATIVES_MAX = 5
ATTENTE_S = 30


@st.cache_resource
def initialiser_base() -> bool:
    db.init_db()
    return True


def uid() -> int | None:
    return st.session_state.get("user_id")


def jour() -> date:
    return st.session_state.get("jour", date.today())


def profil(j: date | None = None) -> Profil | None:
    u = uid()
    return db.charger_profil(u, j or jour()) if u else None


def deconnecter() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# ---------------------------------------------------------------------------
# Connexion / inscription
# ---------------------------------------------------------------------------
def page_connexion() -> None:
    st.title("🥗 Nutrima")
    st.markdown("**Bouger plus, mieux manger, à tout âge.** Connecte-toi pour retrouver ton suivi.")
    t1, t2 = st.tabs(["Se connecter", "Créer un compte"])

    with t1:
        bloque = st.session_state.get("bloque_jusqua", 0) - time.time()
        with st.form("connexion"):
            nom = st.text_input("Identifiant", autocomplete="username")
            mdp = st.text_input("Mot de passe", type="password", autocomplete="current-password")
            ok = st.form_submit_button("Se connecter", type="primary", width="stretch")
        if ok:
            if bloque > 0:
                st.error(f"Trop de tentatives. Réessaie dans {int(bloque) + 1} s.")
            else:
                try:
                    st.session_state.user_id = auth.connecter(nom, mdp)
                    st.session_state.username = nom.strip()
                    st.session_state.pop("echecs", None)
                    st.rerun()
                except auth.ErreurAuth as e:
                    n = st.session_state.get("echecs", 0) + 1
                    st.session_state.echecs = n
                    if n >= TENTATIVES_MAX:
                        st.session_state.bloque_jusqua = time.time() + ATTENTE_S
                        st.session_state.echecs = 0
                    st.error(str(e))

    with t2:
        with st.form("inscription"):
            nom = st.text_input("Choisis un identifiant", help="3 à 30 caractères : lettres, chiffres, . _ -",
                                autocomplete="username")
            mdp = st.text_input("Mot de passe", type="password", help="8 caractères minimum, lettres et chiffres",
                                autocomplete="new-password")
            mdp2 = st.text_input("Confirme le mot de passe", type="password", autocomplete="new-password")
            ok = st.form_submit_button("Créer mon compte", type="primary", width="stretch")
        if ok:
            try:
                st.session_state.user_id = auth.inscrire(nom, mdp, mdp2)
                st.session_state.username = nom.strip()
                st.rerun()
            except auth.ErreurAuth as e:
                st.error(str(e))
    st.caption("🔒 Les mots de passe sont hachés (bcrypt), jamais stockés en clair. Tes données restent sur le serveur de Nutrima "
               "et ne sont partagées avec personne.")


# ---------------------------------------------------------------------------
# Barre latérale
# ---------------------------------------------------------------------------
def _changer_jour(delta: int) -> None:
    st.session_state.jour = date.today() if delta == 0 else jour() + timedelta(days=delta)


def barre_laterale(p: Profil | None) -> None:
    with st.sidebar:
        nom = (p.prenom if p and p.prenom else None) or st.session_state.get("username", "")
        st.markdown(f"### 👋 Bonjour {nom}")
        if p:
            st.date_input("📅 Jour affiché", key="jour", max_value=date.today(), format="DD/MM/YYYY")
            c1, c2 = st.columns(2)
            c1.button("◀ Veille", width="stretch", on_click=_changer_jour, args=(-1,))
            c2.button("Aujourd'hui", width="stretch", disabled=jour() == date.today(),
                      on_click=_changer_jour, args=(0,))
        st.divider()
        if st.button("Se déconnecter", icon=":material/logout:", width="stretch"):
            deconnecter()
            st.rerun()


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def donnees(u: int, debut: date, fin: date):
    """Activités (7 jours avant le début inclus pour les bilans glissants), aliments et temps assis."""
    act = db.activites(u, debut - timedelta(days=6), fin)
    food = db.aliments(u, debut, fin)
    assis = db.assis(u, debut, fin)
    return act, food, assis


def bilans_periode(u: int, p: Profil, debut: date, fin: date) -> pd.DataFrame:
    act, food, assis = donnees(u, debut, fin)
    lignes = []
    j = debut
    while j <= fin:
        b = bilan(p, j, act, food, assis.get(j))
        f_j = b["f_j"]
        lignes.append({
            "date": j, "score": b["total"],
            "minutes_actives": float(act.loc[(act["date"] == j) & (act["intensite"] != "léger"), "duree"].sum())
            if len(act) else 0.0,
            "kcal": float(f_j["kcal"].sum()) if len(f_j) else None,
            "cible_kcal": round(b["kcal_c"]),
            "portions_fl": float(f_j["portions_fl"].sum()) if len(f_j) else None,
            "assis": assis.get(j),
            "eq_7j": b["eq"],
        })
        j += timedelta(days=1)
    return pd.DataFrame(lignes)


def afficher_message(niveau: str, texte: str) -> None:
    {"ok": st.success, "warn": st.warning, "bad": st.error}.get(niveau, st.info)(texte)


def renommer_aliments(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "repas": "Repas", "aliment": "Aliment", "quantite_g": "Quantité (g)", "categorie": "Catégorie",
        "kcal": "kcal", "proteines": "Protéines (g)", "glucides": "Glucides (g)", "lipides": "Lipides (g)",
        "fibres": "Fibres (g)", "sucres_libres": "Sucres libres (g)", "sel": "Sel (g)",
        "portions_fl": "Portions F&L"})
