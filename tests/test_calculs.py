from datetime import date, timedelta

import pandas as pd
import pytest

from nutrima.calculs import (ACT_COLS, FOOD_COLS, Profil, age_au, bilan, intensite, kcal_activite,
                             niveau, nouvel_aliment, nouvelle_activite, serie_jours)
from nutrima.conseils import conseils

J = date(2026, 11, 26)


def adulte(**kw):
    return Profil(**{"naissance": date(1990, 6, 1), "sexe": "Femme", "taille": 165, "poids": 60, **kw})


def df_act(rows):
    return pd.DataFrame([{"id": i, "tag": None, **r} for i, r in enumerate(rows)], columns=ACT_COLS)


def df_food(rows):
    base = dict(id=0, repas="Déjeuner", code=None, categorie="Autres", kcal=0, proteines=0, glucides=0,
                lipides=0, fibres=0, sucres_libres=0, sel=0, portions_fl=0, quantite_g=100, aliment="x")
    return pd.DataFrame([{**base, **r} for r in rows], columns=FOOD_COLS)


def test_age_avant_et_apres_anniversaire():
    assert age_au(date(2000, 12, 1), date(2026, 11, 30)) == 25
    assert age_au(date(2000, 12, 1), date(2026, 12, 1)) == 26


def test_intensite_seuils():
    assert intensite(2.9) == "léger"
    assert intensite(3.0) == "modéré"
    assert intensite(6.0) == "vigoureux"


def test_kcal_activite_nette():
    # 30 min de marche rapide (MET 4,3) pour 70 kg : (4,3 - 1) × 70 × 0,5
    assert kcal_activite(4.3, 70, 30) == pytest.approx(115.5)
    assert kcal_activite(0.5, 70, 30) == 0


def test_bmr_mifflin():
    p = adulte()  # 36 ans au 26/11/2026
    assert p.age(J) == 36
    assert p.bmr(J) == pytest.approx(10 * 60 + 6.25 * 165 - 5 * 36 - 161)


def test_mineur_pas_de_regime_et_cibles():
    p = Profil(date(2014, 1, 1), "Homme", 150, 40, objectif="Perdre du poids doucement")
    assert p.mineur(J)
    assert p.ajustement(J) == 0
    assert p.cible_hebdo(J) == 420
    assert p.cible_proteines(J) == 40


def test_nouvel_aliment_portions_fl():
    f = nouvel_aliment("Pomme", 160, {"kcal": 50, "fibres": 2}, "Fruits & légumes", 1)
    assert f["kcal"] == 80
    assert f["portions_fl"] == 2
    assert nouvel_aliment("Pain", 160, {"kcal": 250}, "Féculents & légumineuses")["portions_fl"] == 0


def test_bilan_sans_donnees():
    b = bilan(adulte(), J, None, None, None)
    assert b["total"] is None
    assert "Sédentarité" not in b["scores"]


def test_bilan_activite_7_jours_glissants():
    p = adulte()
    act = df_act([
        {"date": J, **nouvelle_activite("Marche rapide", 60, 60)},
        {"date": J - timedelta(days=6), **nouvelle_activite("Course à pied", 30, 60)},   # vigoureux, compte double
        {"date": J - timedelta(days=7), **nouvelle_activite("Marche rapide", 300, 60)},  # hors fenêtre
    ])
    b = bilan(p, J, act, None, None)
    assert b["eq"] == 60 + 2 * 30
    assert b["scores"]["Activité physique"][0] == pytest.approx(40 * 120 / 150)


def test_sedentarite_non_renseignee_pas_comptee():
    act = df_act([{"date": J, **nouvelle_activite("Marche rapide", 150, 60)}])
    b = bilan(adulte(), J, act, None, None)
    assert b["total"] == 100  # 40/40, la sédentarité n'est pas comptée
    b2 = bilan(adulte(), J, act, None, 11)
    assert b2["total"] == round(40 / 60 * 100)


def test_score_nutrition_parfait():
    p = adulte()
    cible = p.base_kcal(J)
    food = df_food([{"date": J, "kcal": cible, "proteines": 60, "fibres": 30, "portions_fl": 5,
                     "lipides": cible * 0.3 / 9, "sucres_libres": 0}])
    b = bilan(p, J, None, food, None)
    assert b["scores"]["Nutrition"][0] == pytest.approx(40)


def test_conseils_sucres_et_sel():
    p = adulte()
    food = df_food([{"date": J, "kcal": 2000, "sucres_libres": 100, "sel": 9, "proteines": 60}])
    b = bilan(p, J, None, food, 5)
    textes = " ".join(t for _, _, t in conseils(p, J, b))
    assert "Sucres libres" in textes
    assert "Sel" in textes
    assert "Temps assis maîtrisé" in textes


def test_conseils_senior_equilibre():
    p = adulte(naissance=date(1950, 1, 1))
    b = bilan(p, J, None, None, None)
    themes = [t for _, _, t in conseils(p, J, b)]
    assert any("équilibre" in t for t in themes)


def test_niveau():
    assert niveau(None) == "—"
    assert niveau(85).startswith("🟢")
    assert niveau(10).startswith("🔴")


def test_serie_jours():
    jours = {J, J - timedelta(days=1), J - timedelta(days=2), J - timedelta(days=4)}
    assert serie_jours(jours, J) == 3
    assert serie_jours(jours - {J}, J) == 2  # aujourd'hui pas encore saisi : la série continue depuis hier
    assert serie_jours(set(), J) == 0
