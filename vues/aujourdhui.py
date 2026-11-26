from datetime import date

import pandas as pd
import streamlit as st

from nutrima import db, ui
from nutrima.calculs import bilan, niveau, serie_jours
from nutrima.conseils import conseils

u, j = ui.uid(), ui.jour()
p = ui.profil(j)
act, food, assis = ui.donnees(u, j, j)
b = bilan(p, j, act, food, assis.get(j))

titre = "Aujourd'hui" if j == date.today() else j.strftime("%d/%m/%Y")
st.title(f"🥗 {titre}")

# ----- En-tête : score, série, profil
c1, c2, c3, c4 = st.columns(4)
c1.metric("Score santé du jour", f"{b['total']} / 100" if b["total"] is not None else "—",
          help="40 pts activité (7 jours glissants), 20 pts sédentarité, 40 pts nutrition. "
               "Les parties sans données ne sont pas comptées.")
serie = serie_jours(db.jours_avec_saisie(u), date.today())
c2.metric("Série en cours", f"{serie} jour{'s' if serie > 1 else ''}", help="Jours consécutifs avec au moins une saisie")
c3.metric("IMC", f"{p.imc:.1f}", help=p.interpretation_imc(j))
c4.metric("Besoin estimé du jour", f"{b['kcal_c']:.0f} kcal",
          help="Métabolisme de base × 1,2, plus la dépense des activités saisies, ajusté selon l'objectif.")

if b["total"] is None:
    st.info("Rien de saisi pour ce jour. Commence par ajouter une activité, ton temps assis ou un repas.")
    c1, c2 = st.columns(2)
    c1.page_link("vues/activite.py", label="Saisir une activité", icon=":material/directions_run:")
    c2.page_link("vues/alimentation.py", label="Saisir un repas", icon=":material/restaurant:")
else:
    st.markdown(f"#### {niveau(b['total'])}")
    st.progress(b["total"] / 100)
    cols = st.columns(3)
    for col, nom in zip(cols, ["Activité physique", "Sédentarité", "Nutrition"]):
        with col.container(border=True):
            if nom in b["scores"]:
                pts, mx = b["scores"][nom]
                st.metric(nom, f"{pts:.0f} / {mx}")
                st.progress(min(1.0, pts / mx))
            else:
                st.metric(nom, "—")
                st.caption("Pas encore de données")

# ----- Objectifs de la semaine
st.subheader("🎯 Objectifs sur 7 jours")
c1, c2, c3 = st.columns(3)
cible = b["cible_hebdo"]
with c1.container(border=True):
    st.markdown(f"**Activité** : {int(b['eq'])} / {cible} min")
    st.progress(min(1.0, b["eq"] / cible))
    st.caption(p.texte_cible(j))
with c2.container(border=True):
    obj_renfo = 3 if p.mineur(j) else 2
    st.markdown(f"**Renforcement** : {b['renfo']} / {obj_renfo} séances")
    st.progress(min(1.0, b["renfo"] / obj_renfo))
with c3.container(border=True):
    if p.senior(j):
        st.markdown(f"**Équilibre** : {b['equilibre']} / 3 séances")
        st.progress(min(1.0, b["equilibre"] / 3))
    else:
        fl = b["tot"]["portions_fl"]
        st.markdown(f"**Fruits & légumes du jour** : {fl:.1f} / 5")
        st.progress(min(1.0, fl / 5))

# ----- Répartition des nutriments
if b["n_food"]:
    t = b["tot"]
    st.subheader("🍽️ Nutrition du jour")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"**{t['kcal']:.0f} kcal** consommées sur environ {b['kcal_c']:.0f}")
        st.progress(min(1.0, t["kcal"] / b["kcal_c"]) if b["kcal_c"] else 0.0)
        macro = pd.DataFrame({"Nutriment": ["Protéines", "Glucides", "Lipides"],
                              "Part de l'énergie (%)": [t["proteines"] * 4, t["glucides"] * 4, t["lipides"] * 9]})
        total_macro = macro["Part de l'énergie (%)"].sum() or 1
        macro["Part de l'énergie (%)"] = (macro["Part de l'énergie (%)"] / total_macro * 100).round()
        st.bar_chart(macro, x="Nutriment", y="Part de l'énergie (%)", horizontal=True, height=180)
    with c2:
        par_repas = b["f_j"].groupby("repas", as_index=False)["kcal"].sum()
        st.markdown("**Énergie par repas (kcal)**")
        st.bar_chart(par_repas, x="repas", y="kcal", x_label="", y_label="kcal", height=230)

# ----- Conseils
st.subheader("💡 Conseils personnalisés")
st.caption(f"Adaptés à ton profil : {p.groupe(j)}")
for niv, theme, txt in conseils(p, j, b):
    ui.afficher_message(niv, f"**{theme}** : {txt}")
st.caption("Ces conseils sont indicatifs et ne remplacent pas l'avis d'un médecin ou d'un diététicien.")
