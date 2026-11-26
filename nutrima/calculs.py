"""Calculs de santé purs (sans Streamlit) : profil, dépenses, bilan et score."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from .referentiels import ACTIVITES, CAT_FL, OBJECTIFS

ACT_COLS = ["id", "date", "nom", "duree", "intensite", "kcal", "tag"]
FOOD_COLS = ["id", "date", "repas", "aliment", "code", "quantite_g", "categorie", "kcal",
             "proteines", "glucides", "lipides", "fibres", "sucres_libres", "sel", "portions_fl"]
NUTRIMENTS = ["kcal", "proteines", "glucides", "lipides", "fibres", "sucres_libres", "sel", "portions_fl"]

PORTION_FL_G = 80      # 1 portion de fruits ou légumes ≈ 80 g (PNNS)
SEL_MAX_G = 5          # OMS : moins de 5 g de sel par jour (adulte)


def age_au(naissance: date, jour: date) -> int:
    return jour.year - naissance.year - ((jour.month, jour.day) < (naissance.month, naissance.day))


def intensite(met: float) -> str:
    return "léger" if met < 3 else ("modéré" if met < 6 else "vigoureux")


def kcal_activite(met: float, poids: float, duree_min: float) -> float:
    """Dépense nette liée à l'activité (MET - 1, le repos étant déjà compté dans le métabolisme)."""
    return max(met - 1, 0) * poids * duree_min / 60


@dataclass
class Profil:
    naissance: date
    sexe: str
    taille: float          # cm
    poids: float           # kg
    objectif: str = "Maintenir mon poids"
    prenom: str = ""

    def age(self, jour: date | None = None) -> int:
        return age_au(self.naissance, jour or date.today())

    def mineur(self, jour: date | None = None) -> bool:
        return self.age(jour) < 18

    def senior(self, jour: date | None = None) -> bool:
        return self.age(jour) >= 65

    @property
    def imc(self) -> float:
        return self.poids / ((self.taille / 100) ** 2)

    def bmr(self, jour: date | None = None) -> float:
        """Métabolisme de base, équation de Mifflin-St Jeor."""
        return 10 * self.poids + 6.25 * self.taille - 5 * self.age(jour) + (5 if self.sexe == "Homme" else -161)

    def base_kcal(self, jour: date | None = None) -> float:
        return self.bmr(jour) * 1.2  # métabolisme + vie quotidienne sédentaire

    def ajustement(self, jour: date | None = None) -> int:
        if self.mineur(jour):
            return 0  # pas de régime pour les moins de 18 ans
        return OBJECTIFS.get(self.objectif, 0)

    def groupe(self, jour: date | None = None) -> str:
        a = self.age(jour)
        if a < 18:
            return "Enfant / adolescent (5-17 ans)"
        if a < 65:
            return "Adulte (18-64 ans)"
        return "Senior (65 ans et +)"

    def cible_hebdo(self, jour: date | None = None) -> int:
        """Minutes hebdomadaires d'activité (équivalent modéré) recommandées par l'OMS."""
        return 420 if self.mineur(jour) else 150

    def texte_cible(self, jour: date | None = None) -> str:
        a = self.age(jour)
        if a < 18:
            return "60 min/jour d'activité modérée à intense"
        if a < 65:
            return "150 à 300 min/semaine d'activité modérée + 2 séances de renforcement"
        return "150 à 300 min/semaine + renforcement et 3 séances d'équilibre"

    def cible_fibres(self, jour: date | None = None) -> int:
        return 20 if self.mineur(jour) else 25

    def cible_proteines(self, jour: date | None = None) -> float:
        return self.poids * (1.0 if (self.mineur(jour) or self.senior(jour)) else 0.83)

    def interpretation_imc(self, jour: date | None = None) -> str:
        if self.mineur(jour):
            return ("L'IMC des moins de 18 ans s'interprète avec des courbes de croissance : "
                    "demande conseil à un professionnel de santé.")
        i = self.imc
        if i < 18.5:
            return "IMC inférieur à 18,5 : corpulence faible."
        if i < 25:
            return "IMC entre 18,5 et 25 : corpulence normale."
        if i < 30:
            return "IMC entre 25 et 30 : surpoids."
        return "IMC supérieur à 30 : obésité. Un avis médical est recommandé."


def nouvelle_activite(nom: str, duree: int, poids: float) -> dict:
    met, tag = ACTIVITES[nom]
    return {"nom": nom, "duree": int(duree), "intensite": intensite(met),
            "kcal": round(kcal_activite(met, poids, duree)), "tag": tag}


def nouvel_aliment(aliment: str, quantite_g: float, valeurs_100g: dict, categorie: str,
                   code: int | None = None) -> dict:
    """Calcule les apports d'une portion à partir des valeurs pour 100 g."""
    r = quantite_g / 100
    out = {"aliment": aliment, "code": code, "quantite_g": quantite_g, "categorie": categorie}
    for k in ["kcal", "proteines", "glucides", "lipides", "fibres", "sucres_libres", "sel"]:
        out[k] = round(float(valeurs_100g.get(k, 0) or 0) * r, 2)
    out["portions_fl"] = round(quantite_g / PORTION_FL_G, 2) if categorie == CAT_FL else 0.0
    return out


def aliment_manuel(nom: str, quantite_g: float, totaux: dict) -> dict:
    """Plat saisi à la main : les valeurs fournies sont celles de la portion entière."""
    out = {"aliment": nom, "code": None, "quantite_g": quantite_g, "categorie": "Saisie manuelle"}
    for k in ["kcal", "proteines", "glucides", "lipides", "fibres", "sucres_libres", "sel"]:
        out[k] = round(float(totaux.get(k, 0) or 0), 2)
    out["portions_fl"] = round(float(totaux.get("portions_fl", 0) or 0), 2)
    return out


# ---------------------------------------------------------------------------
# BILAN
# ---------------------------------------------------------------------------
def _vide(cols):
    return pd.DataFrame(columns=cols)


def cible_kcal(profil: Profil, jour: date, act: pd.DataFrame) -> float:
    kcal_act = act.loc[act["date"] == jour, "kcal"].sum() if len(act) else 0
    return profil.base_kcal(jour) + kcal_act + profil.ajustement(jour)


def bilan(profil: Profil, jour: date, act: pd.DataFrame | None, food: pd.DataFrame | None,
          assis_h: float | None) -> dict:
    """Bilan d'une journée : activité sur 7 jours glissants, nutrition et sédentarité du jour."""
    act = act if act is not None and len(act) else _vide(ACT_COLS)
    food = food if food is not None and len(food) else _vide(FOOD_COLS)
    mineur = profil.mineur(jour)
    cible_hebdo = profil.cible_hebdo(jour)

    debut = jour - timedelta(days=6)
    a_sem = act[(act["date"] >= debut) & (act["date"] <= jour)]
    f_j = food[food["date"] == jour]

    mod = float(a_sem.loc[a_sem["intensite"] == "modéré", "duree"].sum())
    vig = float(a_sem.loc[a_sem["intensite"] == "vigoureux", "duree"].sum())
    eq = mod + vig if mineur else mod + 2 * vig  # OMS : 1 min vigoureuse ≈ 2 min modérées (adulte)
    renfo = int((a_sem["tag"] == "renfo").sum())
    equilibre = int((a_sem["tag"] == "equilibre").sum())

    tot = f_j[NUTRIMENTS].astype(float).sum() if len(f_j) else pd.Series(0.0, index=NUTRIMENTS)
    kcal_c = cible_kcal(profil, jour, act)

    scores: dict[str, tuple[float, int]] = {}
    scores["Activité physique"] = (40 * min(1.0, eq / cible_hebdo), 40)
    if assis_h is not None:
        scores["Sédentarité"] = (20 * max(0.0, min(1.0, (11 - assis_h) / 5)), 20)

    pct_sucres = pct_lip = 0.0
    if len(f_j) and tot["kcal"] > 0:
        r = tot["kcal"] / kcal_c
        pct_sucres = tot["sucres_libres"] * 4 / tot["kcal"] * 100
        pct_lip = tot["lipides"] * 9 / tot["kcal"] * 100
        p_k = 15 * max(0.0, 1 - abs(1 - r) / 0.4)
        p_fl = 10 * min(1.0, tot["portions_fl"] / 5)
        p_fib = 5 * min(1.0, tot["fibres"] / profil.cible_fibres(jour))
        p_su = 5.0 if pct_sucres <= 10 else 5 * max(0.0, 1 - (pct_sucres - 10) / 10)
        p_pr = 5 * min(1.0, tot["proteines"] / profil.cible_proteines(jour))
        scores["Nutrition"] = (p_k + p_fl + p_fib + p_su + p_pr, 40)

    pts = sum(v[0] for v in scores.values())
    mx = sum(v[1] for v in scores.values())
    # Un score n'a de sens que si la journée contient au moins une saisie
    a_des_donnees = len(f_j) > 0 or assis_h is not None or len(act[act["date"] == jour]) > 0
    total = round(pts / mx * 100) if (mx and a_des_donnees) else None

    return dict(eq=eq, mod=mod, vig=vig, renfo=renfo, equilibre=equilibre, assis=assis_h,
                tot=tot, kcal_c=kcal_c, scores=scores, total=total, f_j=f_j, a_sem=a_sem,
                pct_sucres=pct_sucres, pct_lip=pct_lip, n_food=len(f_j), cible_hebdo=cible_hebdo)


def niveau(score: int | None) -> str:
    if score is None:
        return "—"
    if score >= 80:
        return "🟢 Excellent"
    if score >= 60:
        return "🟡 Bien"
    if score >= 40:
        return "🟠 À améliorer"
    return "🔴 Priorité santé"


def serie_jours(jours_actifs: set[date], aujourd_hui: date) -> int:
    """Nombre de jours consécutifs avec au moins une saisie, jusqu'à aujourd'hui (ou hier)."""
    j = aujourd_hui if aujourd_hui in jours_actifs else aujourd_hui - timedelta(days=1)
    n = 0
    while j in jours_actifs:
        n += 1
        j -= timedelta(days=1)
    return n
