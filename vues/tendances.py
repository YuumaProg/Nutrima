from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

from nutrima import db, ui

u, j = ui.uid(), ui.jour()
p = ui.profil(j)

st.title("📈 Tendances")
duree = st.segmented_control("Période", [7, 30, 90], default=30, format_func=lambda n: f"{n} jours",
                             key="periode") or 30
debut = j - timedelta(days=duree - 1)
df = ui.bilans_periode(u, p, debut, j)
df["date"] = pd.to_datetime(df["date"])

jours_saisis = int(df["score"].notna().sum())
c = st.columns(4)
c[0].metric("Score moyen", f"{df['score'].mean():.0f}" if jours_saisis else "—")
c[1].metric("Jours renseignés", f"{jours_saisis} / {duree}")
c[2].metric("Activité moyenne", f"{df['minutes_actives'].mean():.0f} min/jour")
c[3].metric("Fruits & légumes moyens", f"{df['portions_fl'].mean():.1f} / jour" if df["portions_fl"].notna().any() else "—")

if not jours_saisis:
    st.info("Pas encore de données sur cette période.")
    st.stop()

axe_x = alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m"))

st.subheader("Score santé")
score = df.dropna(subset=["score"])
st.altair_chart(
    alt.Chart(score).mark_line(point=True).encode(
        axe_x, alt.Y("score:Q", title="Score", scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), "score:Q"]).properties(height=220),
    width="stretch")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Activité modérée à intense")
    cible_jour = p.cible_hebdo(j) / 7
    barres = alt.Chart(df).mark_bar().encode(
        axe_x, alt.Y("minutes_actives:Q", title="min"),
        tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), alt.Tooltip("minutes_actives:Q", title="min")])
    ligne = alt.Chart(pd.DataFrame({"y": [cible_jour]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
    st.altair_chart((barres + ligne).properties(height=240), width="stretch")
    st.caption(f"Pointillés : repère moyen de {cible_jour:.0f} min/jour.")
with c2:
    st.subheader("Apport énergétique et besoin")
    k = df.dropna(subset=["kcal"]).melt(id_vars="date", value_vars=["kcal", "cible_kcal"],
                                        var_name="série", value_name="valeur")
    k["série"] = k["série"].map({"kcal": "Apport", "cible_kcal": "Besoin estimé"})
    st.altair_chart(
        alt.Chart(k).mark_line(point=True).encode(
            axe_x, alt.Y("valeur:Q", title="kcal"), alt.Color("série:N", title=None, legend=alt.Legend(orient="bottom")),
            tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), "série:N", alt.Tooltip("valeur:Q", format=".0f")]
        ).properties(height=240), width="stretch")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Poids")
    hist = db.historique_poids(u)
    hist = hist[hist["date"] >= debut - timedelta(days=30)]
    if len(hist) < 2:
        st.caption("Ajoute plusieurs pesées dans « Mon profil » pour voir l'évolution.")
    else:
        hist["date"] = pd.to_datetime(hist["date"])
        st.altair_chart(
            alt.Chart(hist).mark_line(point=True).encode(
                axe_x, alt.Y("kg:Q", title="kg", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), "kg:Q"]).properties(height=220),
            width="stretch")
with c2:
    st.subheader("Temps assis")
    a = df.dropna(subset=["assis"])
    if a.empty:
        st.caption("Aucun temps assis renseigné sur la période.")
    else:
        st.altair_chart(
            alt.Chart(a).mark_bar(color="#e4a03d").encode(
                axe_x, alt.Y("assis:Q", title="heures"),
                tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y"), alt.Tooltip("assis:Q", title="h")]
            ).properties(height=220), width="stretch")
