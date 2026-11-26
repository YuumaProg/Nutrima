"""
Crée (ou recrée) un compte de démonstration avec 30 jours de données réalistes.

Usage :  python scripts/creer_demo.py
Compte : identifiant « demo », mot de passe « demo1234 » (à ne pas utiliser en production).
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nutrima import aliments as base  # noqa: E402
from nutrima import auth, db  # noqa: E402
from nutrima.calculs import nouvel_aliment, nouvelle_activite  # noqa: E402

NOM, MDP = "demo", "demo1234"

# (repas, code Ciqual, grammes)
MENUS = [
    [("Petit-déjeuner", 7000, 80), ("Petit-déjeuner", 19593, 125), ("Déjeuner", 9811, 250),
     ("Déjeuner", 36018, 120), ("Déjeuner", 20276, 120), ("Collation", 13039, 150),
     ("Dîner", 25404, 250), ("Dîner", 20030, 150)],
    [("Petit-déjeuner", 9310, 50), ("Petit-déjeuner", 19041, 200), ("Petit-déjeuner", 13005, 120),
     ("Déjeuner", 9104, 180), ("Déjeuner", 26038, 130), ("Déjeuner", 20030, 150),
     ("Collation", 31004, 40), ("Collation", 18026, 330), ("Dîner", 25416, 280)],
]


def main() -> None:
    db.init_db()
    ancien = db.utilisateur_par_nom(NOM)
    if ancien:
        db.supprimer_utilisateur(ancien["id"])
    u = db.creer_utilisateur(NOM, auth.hacher(MDP))
    db.enregistrer_profil(u, "Camille", date(1990, 5, 14), "Femme", 168, "Perdre du poids doucement")
    random.seed(3)
    t = base.table()
    codes = set(t["code"])
    auj = date.today()
    for i in range(30, -1, -1):
        d = auj - timedelta(days=i)
        poids = 72 - (30 - i) * 0.05 + random.uniform(-0.3, 0.3)
        if i % 3 == 0:
            db.enregistrer_poids(u, d, round(poids, 1))
        if random.random() < 0.6:
            nom = random.choice(["Marche rapide", "Vélo (loisir / trajet)", "Natation", "Danse"])
            db.ajouter_activite(u, d, nouvelle_activite(nom, random.choice([20, 30, 45]), poids))
        if d.weekday() in (1, 4):
            db.ajouter_activite(u, d, nouvelle_activite("Renforcement au poids du corps", 25, poids))
        db.enregistrer_assis(u, d, random.choice([6, 7, 8, 8.5, 9, 10]))
        for repas, code, g in random.choice(MENUS):
            if code not in codes:
                continue
            al = base.par_code(code)
            db.ajouter_aliment(u, d, repas, nouvel_aliment(al["nom"], g * random.uniform(0.8, 1.2) // 5 * 5,
                                                           al.to_dict(), al["categorie"], code))
    print(f"Compte de démonstration prêt : {NOM} / {MDP}")


if __name__ == "__main__":
    main()
