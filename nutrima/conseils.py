"""Conseils personnalisés selon l'âge et le bilan du jour."""
from __future__ import annotations

from datetime import date

from .calculs import SEL_MAX_G, Profil
from .referentiels import CAT_LAITIERS, CAT_TRANSFO

# Niveaux : "ok", "warn", "bad", "info"


def conseils(profil: Profil, jour: date, b: dict) -> list[tuple[str, str, str]]:
    """Retourne une liste de (niveau, thème, texte)."""
    out: list[tuple[str, str, str]] = []
    age = profil.age(jour)
    mineur = age < 18
    senior = age >= 65
    cible = b["cible_hebdo"]

    # --- Activité
    if b["eq"] >= cible:
        out.append(("ok", "Activité", f"Objectif atteint sur 7 jours ({int(b['eq'])} min équivalent modéré). Continue !"))
    else:
        manque = int(cible - b["eq"])
        if mineur:
            idee = "jeux actifs, trajet à pied ou à vélo vers l'école, sport avec des amis ou en club."
        elif not senior:
            idee = "marche rapide de 30 min 5 fois par semaine, vélo pour les trajets, escaliers plutôt qu'ascenseur."
        else:
            idee = "marche quotidienne, jardinage, aquagym, danse : l'important est de bouger régulièrement."
        out.append(("bad" if b["eq"] < cible / 2 else "warn", "Activité",
                    f"Il manque environ {manque} min d'activité sur les 7 derniers jours. Idées : {idee}"))
    if mineur and b["renfo"] < 3:
        out.append(("warn", "Activité", "Pour les jeunes, 3 séances par semaine qui renforcent muscles et os (sauts, grimper, sports de ballon)."))
    elif not mineur and b["renfo"] < 2:
        out.append(("warn", "Activité", "Ajoute 2 séances de renforcement musculaire par semaine (poids du corps, élastiques, musculation)."))
    if senior and b["equilibre"] < 3:
        out.append(("warn", "Activité", "À partir de 65 ans, 3 séances d'équilibre par semaine (tai-chi, marche sur une ligne, appui sur un pied) réduisent le risque de chute."))

    # --- Sédentarité
    assis = b["assis"]
    if assis is None:
        out.append(("info", "Sédentarité", "Renseigne ton temps assis du jour (onglet Activité) pour obtenir un conseil personnalisé."))
    elif assis >= 9:
        out.append(("bad", "Sédentarité", f"{assis:g} h assis : c'est beaucoup. Lève-toi 2 à 5 min toutes les 30 à 60 min (appel debout, verre d'eau, étirements)."))
    elif assis > 6:
        out.append(("warn", "Sédentarité", f"{assis:g} h assis : essaie de fractionner ce temps avec de courtes pauses actives."))
    else:
        out.append(("ok", "Sédentarité", "Temps assis maîtrisé, bravo !"))
    if mineur and assis is not None and assis > 2:
        out.append(("warn", "Écrans", "Pour les jeunes, les recommandations visent à limiter les écrans de loisir à environ 2 h par jour."))

    # --- Nutrition
    if b["n_food"] == 0:
        out.append(("info", "Nutrition", "Aucun aliment saisi pour ce jour : ajoute tes repas pour obtenir un bilan nutritionnel."))
        return out
    t = b["tot"]
    r = t["kcal"] / b["kcal_c"] if b["kcal_c"] else 1
    if r > 1.15:
        out.append(("warn", "Nutrition", f"Apport de {t['kcal']:.0f} kcal pour une cible d'environ {b['kcal_c']:.0f} : réduis les portions ou les produits très gras ou sucrés."))
    elif r < 0.8:
        out.append(("warn", "Nutrition", f"Apport de {t['kcal']:.0f} kcal pour une cible d'environ {b['kcal_c']:.0f} : attention à ne pas manger trop peu (fatigue, perte musculaire). As-tu tout saisi ?"))
    else:
        out.append(("ok", "Nutrition", "Apport énergétique cohérent avec ta dépense."))
    if t["portions_fl"] < 5:
        out.append(("warn", "Nutrition", f"{t['portions_fl']:.1f} portion(s) de fruits et légumes sur 5 recommandées (1 portion ≈ 80 g)."))
    else:
        out.append(("ok", "Nutrition", "5 fruits et légumes par jour : objectif atteint."))
    cf = profil.cible_fibres(jour)
    if t["fibres"] < cf:
        out.append(("warn", "Nutrition", f"Fibres : {t['fibres']:.0f} g sur {cf} g. Privilégie pain complet, légumineuses, flocons d'avoine."))
    if b["pct_sucres"] > 10:
        out.append(("bad", "Nutrition", f"Sucres libres : environ {b['pct_sucres']:.0f} % de l'énergie (l'OMS recommande moins de 10 %). Remplace sodas et jus par de l'eau."))
    if b["pct_lip"] > 40:
        out.append(("warn", "Nutrition", f"Lipides : {b['pct_lip']:.0f} % de l'énergie (repère : 35 à 40 % maximum). Limite fritures et charcuteries."))
    sel_max = SEL_MAX_G if not mineur else 4
    if t["sel"] > sel_max:
        out.append(("warn", "Nutrition", f"Sel : {t['sel']:.1f} g (repère : moins de {sel_max} g/jour). Limite plats préparés, charcuterie et fromages salés, goûte avant de saler."))
    cp = profil.cible_proteines(jour)
    if t["proteines"] < cp * 0.8:
        extra = " Après 65 ans, les protéines aident à conserver la masse musculaire." if senior else ""
        out.append(("warn", "Nutrition", f"Protéines : {t['proteines']:.0f} g pour une cible d'environ {cp:.0f} g. Ajoute œufs, poisson, légumineuses ou produits laitiers.{extra}"))
    f_j = b["f_j"]
    transfo = f_j.loc[f_j["categorie"] == CAT_TRANSFO, "quantite_g"].sum()
    if transfo > 150:
        out.append(("warn", "Nutrition", f"{int(transfo)} g de produits sucrés/transformés aujourd'hui : garde-les pour de petits plaisirs occasionnels."))
    if senior and not (f_j["categorie"] == CAT_LAITIERS).any():
        out.append(("warn", "Nutrition", "Pense aux produits laitiers (calcium) pour la santé des os, et à la vitamine D."))
    out.append(("info", "Hydratation", "Bois de l'eau régulièrement (environ 1,5 L/jour), sans attendre d'avoir soif, surtout après 65 ans."))
    return out
