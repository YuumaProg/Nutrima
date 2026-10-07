"""
VitaActive – Lutter contre la sédentarité à tout âge (ODD 3 : bonne santé et bien-être)
Projet GEII – Streamlit
"""
import random
from datetime import date, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="VitaActive", page_icon="🏃", layout="wide")

# ---------------------------------------------------------------------------
# BASES DE DONNÉES (valeurs moyennes approximatives, à vérifier / sourcer : Ciqual ANSES)
# ---------------------------------------------------------------------------
# Activités : nom -> (MET, tag)   tag : "renfo" (renforcement musculaire), "equilibre" ou None
ACTIVITES = {
    "Marche lente / promenade": (2.8, None),
    "Marche rapide": (4.3, None),
    "Randonnée": (6.0, None),
    "Course à pied": (8.3, None),
    "Vélo (loisir / trajet)": (5.8, None),
    "Vélo soutenu": (8.0, None),
    "Natation": (6.0, None),
    "Aquagym": (5.5, None),
    "Danse": (5.0, None),
    "Sports collectifs (foot, basket...)": (7.0, None),
    "Jeux actifs / récréation": (4.5, None),
    "Trottinette / roller": (7.0, None),
    "Yoga": (2.5, None),
    "Pilates": (3.0, None),
    "Tai-chi / exercices d'équilibre": (3.0, "equilibre"),
    "Musculation": (5.0, "renfo"),
    "Renforcement au poids du corps": (4.0, "renfo"),
    "Jardinage": (3.8, None),
    "Ménage actif": (3.3, None),
}

# Aliments pour 100 g : (catégorie, kcal, protéines, glucides, lipides, fibres, sucres libres)
FOODS = {
    # Fruits & légumes
    "Pomme": ("Fruits & légumes", 52, 0.3, 14, 0.2, 2.4, 0),
    "Banane": ("Fruits & légumes", 89, 1.1, 23, 0.3, 2.6, 0),
    "Orange": ("Fruits & légumes", 47, 0.9, 12, 0.1, 2.4, 0),
    "Fraises": ("Fruits & légumes", 32, 0.7, 8, 0.3, 2.0, 0),
    "Carotte": ("Fruits & légumes", 41, 0.9, 10, 0.2, 2.8, 0),
    "Tomate": ("Fruits & légumes", 18, 0.9, 3.9, 0.2, 1.2, 0),
    "Salade verte": ("Fruits & légumes", 15, 1.4, 2.9, 0.2, 1.3, 0),
    "Brocoli (cuit)": ("Fruits & légumes", 35, 2.4, 7, 0.4, 3.3, 0),
    "Haricots verts (cuits)": ("Fruits & légumes", 31, 1.8, 7, 0.2, 3.4, 0),
    "Courgette (cuite)": ("Fruits & légumes", 17, 1.2, 3.1, 0.3, 1.0, 0),
    "Épinards (cuits)": ("Fruits & légumes", 23, 3.0, 3.6, 0.3, 2.4, 0),
    # Féculents & légumineuses
    "Pâtes (cuites)": ("Féculents & légumineuses", 131, 5, 25, 1.1, 1.8, 0),
    "Riz blanc (cuit)": ("Féculents & légumineuses", 130, 2.7, 28, 0.3, 0.4, 0),
    "Riz complet (cuit)": ("Féculents & légumineuses", 123, 2.7, 26, 1.0, 1.8, 0),
    "Pain blanc": ("Féculents & légumineuses", 265, 9, 49, 3.2, 2.7, 0),
    "Pain complet": ("Féculents & légumineuses", 250, 9, 43, 3.5, 7.0, 0),
    "Pommes de terre (cuites)": ("Féculents & légumineuses", 86, 1.7, 20, 0.1, 1.8, 0),
    "Flocons d'avoine": ("Féculents & légumineuses", 370, 13, 60, 7, 10, 0),
    "Lentilles (cuites)": ("Féculents & légumineuses", 116, 9, 20, 0.4, 7.9, 0),
    "Pois chiches (cuits)": ("Féculents & légumineuses", 164, 8.9, 27, 2.6, 7.6, 0),
    # Protéines
    "Poulet (grillé)": ("Viandes, poissons, œufs", 165, 31, 0, 3.6, 0, 0),
    "Œuf (cuit)": ("Viandes, poissons, œufs", 155, 13, 1.1, 11, 0, 0),
    "Saumon (cuit)": ("Viandes, poissons, œufs", 206, 22, 0, 12, 0, 0),
    "Thon (conserve)": ("Viandes, poissons, œufs", 116, 26, 0, 1, 0, 0),
    "Bœuf haché 5% (cuit)": ("Viandes, poissons, œufs", 190, 26, 0, 9, 0, 0),
    "Jambon blanc": ("Viandes, poissons, œufs", 110, 19, 1, 3, 0, 0),
    "Tofu": ("Viandes, poissons, œufs", 76, 8, 1.9, 4.8, 0.3, 0),
    # Produits laitiers
    "Yaourt nature": ("Produits laitiers", 59, 3.5, 4.7, 3.3, 0, 0),
    "Lait demi-écrémé": ("Produits laitiers", 46, 3.3, 4.8, 1.6, 0, 0),
    "Fromage (emmental)": ("Produits laitiers", 380, 28, 0, 29, 0, 0),
    "Fromage blanc 0%": ("Produits laitiers", 45, 8, 4, 0.2, 0, 0),
    # Matières grasses & oléagineux
    "Huile d'olive": ("Matières grasses & oléagineux", 884, 0, 0, 100, 0, 0),
    "Beurre": ("Matières grasses & oléagineux", 717, 0.9, 0.1, 81, 0, 0),
    "Amandes": ("Matières grasses & oléagineux", 579, 21, 22, 50, 12, 0),
    # Produits sucrés / transformés
    "Pizza": ("Produits sucrés / transformés", 266, 11, 33, 10, 2.3, 3),
    "Hamburger (fast-food)": ("Produits sucrés / transformés", 250, 13, 24, 11, 1.5, 5),
    "Frites": ("Produits sucrés / transformés", 312, 3.4, 41, 15, 3.8, 0),
    "Chips": ("Produits sucrés / transformés", 536, 6.6, 53, 34, 4.4, 0),
    "Chocolat au lait": ("Produits sucrés / transformés", 535, 7.7, 59, 30, 3, 52),
    "Biscuits sucrés": ("Produits sucrés / transformés", 480, 6, 70, 19, 2, 25),
    "Croissant": ("Produits sucrés / transformés", 406, 8, 45, 21, 2.4, 11),
    "Glace": ("Produits sucrés / transformés", 207, 3.5, 24, 11, 0.7, 21),
    # Boissons
    "Eau": ("Boissons", 0, 0, 0, 0, 0, 0),
    "Café sans sucre": ("Boissons", 1, 0.1, 0, 0, 0, 0),
    "Soda": ("Boissons", 42, 0, 10.6, 0, 0, 10.6),
    "Jus d'orange": ("Boissons", 45, 0.7, 10, 0.2, 0.2, 10),
}

REPAS = ["Petit-déjeuner", "Déjeuner", "Collation", "Dîner"]
ACT_COLS = ["date", "activité", "durée (min)", "intensité", "kcal", "tag"]
FOOD_COLS = ["date", "repas", "aliment", "quantité (g)", "catégorie", "kcal",
             "protéines", "glucides", "lipides", "fibres", "sucres libres", "portions F&L"]


# ---------------------------------------------------------------------------
# ÉTAT DE SESSION
# ---------------------------------------------------------------------------
for key, default in [("activites", []), ("aliments", []), ("assis", {})]:
    if key not in st.session_state:
        st.session_state[key] = default


def df_act():
    return pd.DataFrame(st.session_state.activites, columns=ACT_COLS)


def df_food():
    return pd.DataFrame(st.session_state.aliments, columns=FOOD_COLS)


def intensite(met):
    return "léger" if met < 3 else ("modéré" if met < 6 else "vigoureux")


# ---------------------------------------------------------------------------
# PROFIL (sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🏃 VitaActive")
    st.caption("Bouger plus, mieux manger, à tout âge")
    st.header("👤 Mon profil")
    age = st.number_input("Âge", 5, 100, 35)
    sexe = st.radio("Sexe", ["Femme", "Homme"], horizontal=True)
    poids = st.number_input("Poids (kg)", 15.0, 250.0, 70.0, 0.5)
    taille = st.number_input("Taille (cm)", 100, 220, 170)
    mineur = age < 18
    objectif = st.selectbox(
        "Objectif", ["Maintenir mon poids", "Perdre du poids doucement", "Prendre du poids"],
        disabled=mineur, help="Pour les moins de 18 ans, l'objectif reste « maintenir »."
    )
    if mineur:
        objectif = "Maintenir mon poids"
    jour = st.date_input("📅 Jour de saisie", value=date.today(), max_value=date.today())
    st.divider()
    st.caption("🔒 Aucune donnée n'est enregistrée : tout disparaît à la fermeture de l'onglet.")

# Calculs de profil
imc = poids / ((taille / 100) ** 2)
bmr = 10 * poids + 6.25 * taille - 5 * age + (5 if sexe == "Homme" else -161)
base_kcal = bmr * 1.2  # métabolisme + vie quotidienne sédentaire
ajust = {"Maintenir mon poids": 0, "Perdre du poids doucement": -400, "Prendre du poids": 300}[objectif]

if age < 18:
    groupe = "Enfant / adolescent (5-17 ans)"
    cible_hebdo, unite_cible = 420, "60 min/jour d'activité modérée à intense"
elif age < 65:
    groupe = "Adulte (18-64 ans)"
    cible_hebdo, unite_cible = 150, "150 à 300 min/semaine d'activité modérée"
else:
    groupe = "Senior (65 ans et +)"
    cible_hebdo, unite_cible = 150, "150 à 300 min/semaine + exercices d'équilibre"

cible_fibres = 20 if mineur else 25
cible_prot = poids * (1.0 if (mineur or age >= 65) else 0.83)


def cible_kcal(d):
    a = df_act()
    kcal_act = a.loc[a["date"] == d, "kcal"].sum()
    return base_kcal + kcal_act + ajust


def add_act(d, nom, duree):
    met, tag = ACTIVITES[nom]
    kcal = max(met - 1, 0) * poids * duree / 60  # dépense nette liée à l'activité
    st.session_state.activites.append({
        "date": d, "activité": nom, "durée (min)": duree,
        "intensité": intensite(met), "kcal": round(kcal), "tag": tag})


def add_food(d, repas, nom, g, custom=None):
    if custom:
        cat, k, p, c, l, f, s = "Saisie manuelle", *custom
        fl = 0
    else:
        cat, k100, p100, c100, l100, f100, s100 = FOODS[nom]
        r = g / 100
        k, p, c, l, f, s = k100 * r, p100 * r, c100 * r, l100 * r, f100 * r, s100 * r
        fl = g / 80 if cat == "Fruits & légumes" else 0
    st.session_state.aliments.append({
        "date": d, "repas": repas, "aliment": nom, "quantité (g)": g, "catégorie": cat,
        "kcal": round(k), "protéines": round(p, 1), "glucides": round(c, 1),
        "lipides": round(l, 1), "fibres": round(f, 1), "sucres libres": round(s, 1),
        "portions F&L": round(fl, 2)})


def charger_demo():
    random.seed(7)
    st.session_state.activites, st.session_state.aliments = [], []
    for i in range(7):
        d = jour - timedelta(days=i)
        if i % 2 == 0:
            add_act(d, random.choice(["Marche rapide", "Vélo (loisir / trajet)", "Danse"]), random.choice([20, 30, 40]))
        if i in (1, 4):
            add_act(d, "Renforcement au poids du corps", 25)
        st.session_state.assis[d] = random.choice([7, 8, 9, 10])
        add_food(d, "Petit-déjeuner", "Pain blanc", 80)
        add_food(d, "Petit-déjeuner", "Croissant" if i % 2 else "Yaourt nature", 80 if i % 2 else 125)
        add_food(d, "Déjeuner", "Pâtes (cuites)", 250)
        add_food(d, "Déjeuner", "Poulet (grillé)", 120)
        add_food(d, "Déjeuner", "Tomate" if i % 3 else "Brocoli (cuit)", 120)
        add_food(d, "Collation", "Chocolat au lait", 40)
        add_food(d, "Collation", "Soda", 330)
        add_food(d, "Dîner", "Pizza", 300 if i % 2 else 200)
        add_food(d, "Dîner", "Pomme", 150)


# ---------------------------------------------------------------------------
# BILAN
# ---------------------------------------------------------------------------
def bilan(d):
    adf, fdf = df_act(), df_food()
    debut = d - timedelta(days=6)
    a_sem = adf[(adf["date"] >= debut) & (adf["date"] <= d)]
    f_j = fdf[fdf["date"] == d]

    mod = a_sem.loc[a_sem["intensité"] == "modéré", "durée (min)"].sum()
    vig = a_sem.loc[a_sem["intensité"] == "vigoureux", "durée (min)"].sum()
    eq = mod + vig if mineur else mod + 2 * vig
    renfo = (a_sem["tag"] == "renfo").sum()
    equilibre = (a_sem["tag"] == "equilibre").sum()

    assis = st.session_state.assis.get(d)
    tot = f_j[["kcal", "protéines", "glucides", "lipides", "fibres", "sucres libres", "portions F&L"]].sum()
    kcal_c = cible_kcal(d)

    scores = {}  # nom -> (points, max)
    scores["Activité physique"] = (40 * min(1, eq / cible_hebdo), 40)
    if assis is not None:
        scores["Sédentarité"] = (20 * max(0, min(1, (11 - assis) / 5)), 20)
    pct_sucres = pct_lip = 0
    if len(f_j) > 0 and tot["kcal"] > 0:
        r = tot["kcal"] / kcal_c
        pct_sucres = tot["sucres libres"] * 4 / tot["kcal"] * 100
        pct_lip = tot["lipides"] * 9 / tot["kcal"] * 100
        p_k = 15 * max(0, 1 - abs(1 - r) / 0.4)
        p_fl = 10 * min(1, tot["portions F&L"] / 5)
        p_fib = 5 * min(1, tot["fibres"] / cible_fibres)
        p_su = 5 if pct_sucres <= 10 else 5 * max(0, 1 - (pct_sucres - 10) / 10)
        p_pr = 5 * min(1, tot["protéines"] / cible_prot)
        scores["Nutrition"] = (p_k + p_fl + p_fib + p_su + p_pr, 40)

    pts = sum(v[0] for v in scores.values())
    mx = sum(v[1] for v in scores.values())
    total = round(pts / mx * 100) if mx else None
    return dict(eq=eq, mod=mod, vig=vig, renfo=renfo, equilibre=equilibre, assis=assis,
                tot=tot, kcal_c=kcal_c, scores=scores, total=total, f_j=f_j, a_sem=a_sem,
                pct_sucres=pct_sucres, pct_lip=pct_lip, n_food=len(f_j))


def niveau(s):
    if s is None:
        return "—"
    return "🟢 Excellent" if s >= 80 else "🟡 Bien" if s >= 60 else "🟠 À améliorer" if s >= 40 else "🔴 Priorité santé"


def conseils(b):
    """Retourne une liste de (niveau, thème, texte) : ok / warn / bad."""
    out = []
    # --- Activité
    if b["eq"] >= cible_hebdo:
        out.append(("ok", "Activité", f"Objectif atteint cette semaine ({int(b['eq'])} min équivalent modéré). Continue !"))
    else:
        manque = int(cible_hebdo - b["eq"])
        if mineur:
            idee = "jeux actifs, trajet à pied ou à vélo vers l'école, sport avec des amis ou en club."
        elif age < 65:
            idee = "marche rapide de 30 min 5 fois par semaine, vélo pour les trajets, escaliers plutôt qu'ascenseur."
        else:
            idee = "marche quotidienne, jardinage, aquagym, danse : l'important est de bouger régulièrement."
        out.append(("bad" if b["eq"] < cible_hebdo / 2 else "warn", "Activité",
                    f"Il manque environ {manque} min d'activité cette semaine. Idées : {idee}"))
    if not mineur and b["renfo"] < 2:
        out.append(("warn", "Activité", "Ajoute 2 séances de renforcement musculaire par semaine (poids du corps, élastiques, musculation)."))
    if age >= 65 and b["equilibre"] < 3:
        out.append(("warn", "Activité", "À partir de 65 ans, 3 séances d'équilibre par semaine (tai-chi, marche sur ligne, appui unipodal) réduisent le risque de chute."))
    # --- Sédentarité
    if b["assis"] is None:
        out.append(("warn", "Sédentarité", "Renseigne ton temps assis/écran du jour pour obtenir un conseil personnalisé."))
    elif b["assis"] >= 9:
        out.append(("bad", "Sédentarité", f"{b['assis']} h assis : c'est beaucoup. Lève-toi 2 à 5 min toutes les 30 à 60 min (appel debout, verre d'eau, étirements)."))
    elif b["assis"] > 6:
        out.append(("warn", "Sédentarité", f"{b['assis']} h assis : essaie de fractionner ce temps avec de courtes pauses actives."))
    else:
        out.append(("ok", "Sédentarité", "Temps assis maîtrisé, bravo !"))
    if mineur and b["assis"] is not None and b["assis"] > 2:
        out.append(("warn", "Écrans", "Pour les jeunes, les recommandations visent à limiter les écrans de loisir à environ 2 h/jour."))
    # --- Nutrition
    if b["n_food"] == 0:
        out.append(("warn", "Nutrition", "Aucun aliment saisi pour ce jour : ajoute tes repas pour obtenir un bilan nutritionnel."))
        return out
    t = b["tot"]
    r = t["kcal"] / b["kcal_c"]
    if r > 1.15:
        out.append(("warn", "Nutrition", f"Apport de {int(t['kcal'])} kcal pour une cible d'environ {int(b['kcal_c'])} : réduis les portions ou les produits très gras/sucrés."))
    elif r < 0.8:
        out.append(("warn", "Nutrition", f"Apport de {int(t['kcal'])} kcal pour une cible d'environ {int(b['kcal_c'])} : attention à ne pas manger trop peu (fatigue, perte musculaire)."))
    else:
        out.append(("ok", "Nutrition", "Apport énergétique cohérent avec ta dépense."))
    if t["portions F&L"] < 5:
        out.append(("warn", "Nutrition", f"{t['portions F&L']:.1f} portions de fruits et légumes sur 5 recommandées (1 portion ≈ 80 g)."))
    else:
        out.append(("ok", "Nutrition", "5 fruits et légumes par jour : objectif atteint."))
    if t["fibres"] < cible_fibres:
        out.append(("warn", "Nutrition", f"Fibres : {t['fibres']:.0f} g sur {cible_fibres} g. Privilégie pain complet, légumineuses, flocons d'avoine."))
    if b["pct_sucres"] > 10:
        out.append(("bad", "Nutrition", f"Sucres libres : {b['pct_sucres']:.0f}% de l'énergie (l'OMS recommande moins de 10%). Remplace sodas et jus par de l'eau."))
    if b["pct_lip"] > 40:
        out.append(("warn", "Nutrition", f"Lipides : {b['pct_lip']:.0f}% de l'énergie (repère : 35 à 40% maximum). Limite fritures et charcuteries."))
    if t["protéines"] < cible_prot * 0.8:
        extra = " Après 65 ans, les protéines aident à conserver la masse musculaire." if age >= 65 else ""
        out.append(("warn", "Nutrition", f"Protéines : {t['protéines']:.0f} g pour une cible d'environ {cible_prot:.0f} g. Ajoute œufs, poisson, légumineuses ou produits laitiers.{extra}"))
    transfo = b["f_j"].loc[b["f_j"]["catégorie"] == "Produits sucrés / transformés", "quantité (g)"].sum()
    if transfo > 150:
        out.append(("warn", "Nutrition", f"{int(transfo)} g de produits sucrés/transformés aujourd'hui : garde-les pour de petits plaisirs occasionnels."))
    if age >= 65 and not (b["f_j"]["catégorie"] == "Produits laitiers").any():
        out.append(("warn", "Nutrition", "Pense aux produits laitiers (calcium) pour la santé des os, et à la vitamine D."))
    out.append(("info", "Hydratation", "Bois de l'eau régulièrement (environ 1,5 L/jour), sans attendre d'avoir soif, surtout après 65 ans."))
    return out


# ---------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------
tabs = st.tabs(["🏠 Accueil", "🏃 Activité", "🍽️ Alimentation", "📊 Bilan", "💡 Conseils", "🌍 ODD 3 & à propos"])

# ----- ACCUEIL
with tabs[0]:
    st.title("VitaActive : bouger et bien manger, à tout âge")
    st.markdown(
        "Une appli simple pour **saisir tes activités physiques et ton alimentation**, obtenir un "
        "**bilan santé chiffré** et des **conseils personnalisés selon ton âge**.  \n"
        "Elle contribue à l'**ODD 3** : *donner aux individus les moyens de vivre une vie saine et "
        "promouvoir le bien-être à tous les âges*."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IMC", f"{imc:.1f}")
    c2.metric("Métabolisme de base", f"{bmr:.0f} kcal")
    c3.metric("Besoin de base du jour", f"{base_kcal + ajust:.0f} kcal")
    c4.metric("Profil", groupe.split(" (")[0])
    st.info(f"**Recommandation OMS pour ton profil ({groupe}) :** {unite_cible}.")
    if mineur:
        st.caption("L'IMC des moins de 18 ans s'interprète avec des courbes de croissance : demande conseil à un professionnel de santé.")
    elif imc < 18.5:
        st.caption("IMC inférieur à 18,5 : corpulence faible.")
    elif imc < 25:
        st.caption("IMC entre 18,5 et 25 : corpulence normale.")
    elif imc < 30:
        st.caption("IMC entre 25 et 30 : surpoids.")
    else:
        st.caption("IMC supérieur à 30 : obésité. Un avis médical est recommandé.")

    st.subheader("Comment ça marche ?")
    st.markdown(
        "1. Renseigne ton **profil** dans le menu de gauche.  \n"
        "2. Onglet **Activité** : ajoute tes séances et ton temps assis.  \n"
        "3. Onglet **Alimentation** : ajoute ce que tu as mangé.  \n"
        "4. Consulte ton **Bilan** et tes **Conseils**."
    )
    if st.button("🎬 Charger des données de démonstration (7 jours)"):
        charger_demo()
        st.success("Données de démo chargées, va voir les onglets Bilan et Conseils.")
    if st.button("🗑️ Tout effacer"):
        st.session_state.activites, st.session_state.aliments, st.session_state.assis = [], [], {}
        st.rerun()

# ----- ACTIVITÉ
with tabs[1]:
    st.header(f"Activité physique du {jour.strftime('%d/%m/%Y')}")
    with st.form("f_act", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        act = c1.selectbox("Activité", list(ACTIVITES))
        duree = c2.number_input("Durée (min)", 5, 600, 30, 5)
        if st.form_submit_button("➕ Ajouter l'activité"):
            add_act(jour, act, duree)
            st.success(f"{act} ajoutée.")

    st.subheader("🪑 Temps assis / devant un écran")
    assis_val = st.slider("Heures assis ce jour-là (travail, repas, écrans, transports)", 0, 16,
                          int(st.session_state.assis.get(jour, 6)))
    st.session_state.assis[jour] = assis_val

    a = df_act()
    rows_a = a[a["date"] == jour]
    if rows_a.empty:
        st.caption("Aucune activité saisie pour ce jour.")
    else:
        st.dataframe(rows_a.drop(columns=["date", "tag"]).rename(columns={"kcal": "dépense (kcal)"}), width="stretch")
        c1, c2 = st.columns([2, 1])
        idx = c1.selectbox("Supprimer une ligne", rows_a.index, format_func=lambda i, r=rows_a: f"{r.loc[i, 'activité']} ({r.loc[i, 'durée (min)']} min)")
        if c2.button("🗑️ Supprimer", key="del_act"):
            st.session_state.activites.pop(idx)
            st.rerun()

# ----- ALIMENTATION
with tabs[2]:
    st.header(f"Alimentation du {jour.strftime('%d/%m/%Y')}")
    mode = st.radio("Type de saisie", ["Aliment de la liste", "Saisie manuelle"], horizontal=True)
    with st.form("f_food", clear_on_submit=True):
        c1, c2, c3 = st.columns([1.2, 2, 1])
        repas = c1.selectbox("Repas", REPAS)
        if mode == "Aliment de la liste":
            cat = st.selectbox("Catégorie", sorted({v[0] for v in FOODS.values()}))
            noms = [n for n, v in FOODS.items() if v[0] == cat]
            nom = c2.selectbox("Aliment", noms)
            g = c3.number_input("Quantité (g ou ml)", 10, 1500, 100, 10)
            custom = None
        else:
            nom = c2.text_input("Nom du plat", "Plat maison")
            g = c3.number_input("Quantité (g)", 10, 1500, 300, 10)
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            custom = (m1.number_input("kcal", 0, 3000, 400), m2.number_input("Prot. (g)", 0.0, 200.0, 20.0),
                      m3.number_input("Gluc. (g)", 0.0, 400.0, 40.0), m4.number_input("Lip. (g)", 0.0, 200.0, 15.0),
                      m5.number_input("Fibres (g)", 0.0, 100.0, 4.0), m6.number_input("Sucres libres (g)", 0.0, 200.0, 5.0))
        if st.form_submit_button("➕ Ajouter l'aliment"):
            add_food(jour, repas, nom, g, custom)
            st.success(f"{nom} ajouté.")

    f = df_food()
    rows_f = f[f["date"] == jour]
    if rows_f.empty:
        st.caption("Aucun aliment saisi pour ce jour.")
    else:
        st.dataframe(rows_f.drop(columns=["date"]), width="stretch")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Énergie", f"{rows_f['kcal'].sum():.0f} kcal")
        c2.metric("Protéines", f"{rows_f['protéines'].sum():.0f} g")
        c3.metric("Fibres", f"{rows_f['fibres'].sum():.0f} g")
        c4.metric("Fruits & légumes", f"{rows_f['portions F&L'].sum():.1f} / 5")
        c1, c2 = st.columns([2, 1])
        idx = c1.selectbox("Supprimer une ligne", rows_f.index, format_func=lambda i, r=rows_f: f"{r.loc[i, 'aliment']} ({r.loc[i, 'quantité (g)']} g)", key="sel_food")
        if c2.button("🗑️ Supprimer", key="del_food"):
            st.session_state.aliments.pop(idx)
            st.rerun()

# ----- BILAN
with tabs[3]:
    b = bilan(jour)
    st.header(f"Bilan santé du {jour.strftime('%d/%m/%Y')}")
    if b["total"] is None:
        st.warning("Pas encore de données : saisis une activité, ton temps assis ou ton alimentation (ou charge la démo sur l'accueil).")
    else:
        st.subheader(f"Score global : {b['total']} / 100  {niveau(b['total'])}")
        st.progress(b["total"] / 100)
        cols = st.columns(3)
        for col, nom in zip(cols, ["Activité physique", "Sédentarité", "Nutrition"]):
            if nom in b["scores"]:
                p, m = b["scores"][nom]
                col.metric(nom, f"{p:.0f} / {m}")
                col.progress(min(1.0, p / m))
            else:
                col.metric(nom, "—")
                col.caption("Données manquantes")

        st.subheader("Sur les 7 derniers jours")
        c1, c2, c3 = st.columns(3)
        c1.metric("Minutes actives (éq. modéré)", f"{int(b['eq'])} / {cible_hebdo}")
        c2.metric("Séances de renforcement", int(b["renfo"]))
        c3.metric("Séances d'équilibre", int(b["equilibre"]))

        jours = [jour - timedelta(days=i) for i in range(6, -1, -1)]
        adf, fdf = df_act(), df_food()
        graphe_act = pd.DataFrame(
            {"Minutes d'activité": [adf.loc[(adf["date"] == d) & (adf["intensité"] != "léger"), "durée (min)"].sum() for d in jours]},
            index=[d.strftime("%d/%m") for d in jours])
        graphe_kcal = pd.DataFrame(
            {"Apport (kcal)": [fdf.loc[fdf["date"] == d, "kcal"].sum() for d in jours],
             "Cible (kcal)": [round(cible_kcal(d)) for d in jours]},
            index=[d.strftime("%d/%m") for d in jours])
        g1, g2 = st.columns(2)
        g1.markdown("**Activité modérée/intense par jour (min)**")
        g1.bar_chart(graphe_act)
        g2.markdown("**Apport énergétique vs cible**")
        g2.bar_chart(graphe_kcal)

        if b["n_food"]:
            st.subheader("Répartition des nutriments du jour")
            t = b["tot"]
            macro = pd.DataFrame({"Énergie (kcal)": [t["protéines"] * 4, t["glucides"] * 4, t["lipides"] * 9]},
                                 index=["Protéines", "Glucides", "Lipides"])
            st.bar_chart(macro)

        # Export
        st.download_button("⬇️ Exporter mes activités (CSV)", df_act().drop(columns=["tag"]).to_csv(index=False).encode("utf-8"), "activites.csv", "text/csv")
        st.download_button("⬇️ Exporter mon alimentation (CSV)", df_food().to_csv(index=False).encode("utf-8"), "alimentation.csv", "text/csv")

# ----- CONSEILS
with tabs[4]:
    b = bilan(jour)
    st.header("Conseils personnalisés")
    st.caption(f"Adaptés à ton profil : {groupe}")
    for niv, theme, txt in conseils(b):
        msg = f"**{theme}** : {txt}"
        if niv == "ok":
            st.success(msg)
        elif niv == "warn":
            st.warning(msg)
        elif niv == "bad":
            st.error(msg)
        else:
            st.info(msg)
    st.caption("Ces conseils sont indicatifs et ne remplacent pas l'avis d'un médecin ou d'un diététicien.")

# ----- ODD 3
with tabs[5]:
    st.header("ODD 3 : Bonne santé et bien-être")
    st.markdown(
        "**Objectif :** permettre à chacun de vivre en bonne santé et promouvoir le bien-être à tous les âges.  \n"
        "**Cible visée (3.4) :** réduire la mortalité prématurée due aux maladies non transmissibles "
        "(diabète, maladies cardiovasculaires...) grâce à la prévention, et promouvoir la santé mentale et le bien-être.  \n\n"
        "La sédentarité est un facteur de risque majeur de ces maladies. VitaActive agit sur la **prévention** "
        "en rendant visibles et compréhensibles les habitudes de vie."
    )
    st.subheader("Sources des recommandations utilisées")
    st.markdown(
        "- OMS, *Lignes directrices sur l'activité physique et la sédentarité* (2020)  \n"
        "- PNNS / Santé publique France (5 fruits et légumes par jour, repères nutritionnels)  \n"
        "- ANSES, table Ciqual (composition nutritionnelle) et références nutritionnelles en protéines  \n"
        "- Compendium of Physical Activities (valeurs MET)"
    )
    st.subheader("Périmètre et limites")
    st.markdown(
        "- Estimations basées sur des valeurs moyennes, sans valeur de diagnostic médical.  \n"
        "- Base d'aliments limitée (extensible).  \n"
        "- Données non sauvegardées (respect de la vie privée, pas de base de données)."
    )
