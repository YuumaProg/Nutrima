import streamlit as st

st.title("🌍 ODD 3 : bonne santé et bien-être")
st.markdown(
    "**Objectif :** permettre à chacun de vivre en bonne santé et promouvoir le bien-être à tous les âges.  \n"
    "**Cible visée (3.4) :** réduire la mortalité prématurée due aux maladies non transmissibles "
    "(diabète, maladies cardiovasculaires...) grâce à la prévention, et promouvoir la santé mentale et le bien-être.\n\n"
    "La sédentarité et une alimentation déséquilibrée sont des facteurs de risque majeurs de ces maladies. "
    "Nutrima agit sur la **prévention** en rendant visibles et compréhensibles les habitudes de vie."
)

st.subheader("Comment le score est calculé")
st.markdown(
    "- **Activité physique (40 pts)** : minutes d'activité modérée ou intense sur les 7 derniers jours, "
    "comparées au repère OMS (150 min/semaine pour un adulte, 60 min/jour pour les 5-17 ans). "
    "Chez l'adulte, 1 min intense compte double.  \n"
    "- **Sédentarité (20 pts)** : temps assis du jour (score maximal à 6 h ou moins, nul à 11 h ou plus).  \n"
    "- **Nutrition (40 pts)** : énergie proche du besoin estimé (15), fruits et légumes (10), fibres (5), "
    "sucres libres sous 10 % de l'énergie (5), protéines (5).  \n"
    "Les parties sans données ne sont pas comptées : le score est ramené sur 100."
)

st.subheader("Sources")
st.markdown(
    "- OMS, *Lignes directrices sur l'activité physique et la sédentarité* (2020)  \n"
    "- OMS, *Apport en sucres chez l'adulte et l'enfant* (2015) et repère sel (< 5 g/jour)  \n"
    "- PNNS / Santé publique France (5 fruits et légumes par jour, repères nutritionnels)  \n"
    "- ANSES, [table Ciqual 2025](https://doi.org/10.57745/RDMHWY) de composition nutritionnelle des aliments "
    "(licence Etalab 2.0) et références nutritionnelles en protéines  \n"
    "- Compendium of Physical Activities (valeurs MET)  \n"
    "- Équation de Mifflin-St Jeor (métabolisme de base)"
)

st.subheader("Périmètre et limites")
st.markdown(
    "- Estimations fondées sur des valeurs moyennes, **sans valeur de diagnostic médical**.  \n"
    "- Les sucres libres ne figurent pas dans Ciqual : Nutrima les estime (sucres des boissons, "
    "saccharose des produits transformés).  \n"
    "- Les données sont stockées sur le serveur qui héberge Nutrima. Chaque compte peut exporter "
    "ou supprimer ses données à tout moment depuis « Mon profil »."
)
