"""Données de référence : activités (MET), repas, objectifs."""

# Activités : nom -> (MET, tag). Tag : "renfo" (renforcement musculaire), "equilibre" ou None.
# Source : Compendium of Physical Activities (valeurs moyennes).
ACTIVITES: dict[str, tuple[float, str | None]] = {
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
    "Sports de raquette (tennis, badminton...)": (6.0, None),
    "Jeux actifs / récréation": (4.5, None),
    "Trottinette / roller": (7.0, None),
    "Montée d'escaliers": (4.0, None),
    "Yoga": (2.5, None),
    "Pilates": (3.0, None),
    "Tai-chi / exercices d'équilibre": (3.0, "equilibre"),
    "Musculation": (5.0, "renfo"),
    "Renforcement au poids du corps": (4.0, "renfo"),
    "Gym douce / renforcement senior": (3.5, "renfo"),
    "Jardinage": (3.8, None),
    "Ménage actif": (3.3, None),
}

REPAS = ["Petit-déjeuner", "Déjeuner", "Collation", "Dîner"]

OBJECTIFS = {
    "Maintenir mon poids": 0,
    "Perdre du poids doucement": -400,
    "Prendre du poids": 300,
}

SEXES = ["Femme", "Homme"]

CAT_FL = "Fruits & légumes"
CAT_TRANSFO = "Produits sucrés / transformés"
CAT_LAITIERS = "Produits laitiers"
