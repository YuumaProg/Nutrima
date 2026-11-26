"""
Convertit la table Ciqual (ANSES) au format Excel en un CSV compact utilisé par Nutrima.

Usage :
    python scripts/import_ciqual.py "Table Ciqual 2025_FR_2025_11_03.xlsx"

Source : ANSES, Table de composition nutritionnelle des aliments Ciqual 2025,
https://doi.org/10.57745/RDMHWY (licence Etalab 2.0).
Le fichier produit est data/aliments_ciqual.csv (valeurs pour 100 g).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

SORTIE = Path(__file__).resolve().parent.parent / "data" / "aliments_ciqual.csv"

# Colonnes recherchées (par motif, insensible aux retours à la ligne de l'en-tête Excel)
MOTIFS = {
    "kcal": r"^Energie, R.glement UE .*kcal",
    "proteines": r"^Prot.ines, N x facteur de Jones",
    "glucides": r"^Glucides \(g",
    "lipides": r"^Lipides \(g",
    "sucres": r"^Sucres \(g",
    "saccharose": r"^Saccharose \(g",
    "fibres": r"^Fibres alimentaires",
    "sel": r"^Sel chlorure de sodium",
}

# Sous-groupe Ciqual -> catégorie Nutrima
CATEGORIES = {
    "0201": "Fruits & légumes", "0204": "Fruits & légumes",
    "0202": "Féculents & légumineuses", "0203": "Féculents & légumineuses",
    "0301": "Féculents & légumineuses", "0302": "Féculents & légumineuses",
    "0304": "Féculents & légumineuses",
    "0205": "Matières grasses & oléagineux",
    "0303": "Produits sucrés / transformés",
}
CATEGORIES_GROUPE = {
    "01": "Plats composés",
    "04": "Viandes, poissons, œufs",
    "05": "Produits laitiers",
    "06": "Boissons",
    "07": "Produits sucrés / transformés",
    "08": "Produits sucrés / transformés",
    "09": "Matières grasses & oléagineux",
}


def nettoyer(texte) -> str:
    return " ".join(str(texte).split()) if pd.notna(texte) else ""


def nombre(valeur) -> float | None:
    """Convertit une valeur Ciqual ('1,5', '< 0,2', 'traces', '-') en float (None si inconnue)."""
    if pd.isna(valeur):
        return None
    s = str(valeur).strip().replace(",", ".")
    if s in {"-", ""}:
        return None
    if s.lower() == "traces":
        return 0.0
    if s.startswith("<"):
        try:
            return float(s[1:].strip()) / 2  # valeur sous le seuil : on prend la moitié
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def categorie(grp: str, ssgrp: str) -> str:
    return CATEGORIES.get(ssgrp) or CATEGORIES_GROUPE.get(grp, "Autres")


def sucres_libres(grp: str, ssgrp: str, sucres, saccharose) -> float:
    """Estimation des sucres libres (définition OMS), absente de Ciqual.

    - fruits, légumes, féculents, légumineuses, viandes : sucres naturellement présents -> 0
    - boissons, sucres/miels/confitures : sucres totaux (les jus comptent comme sucres libres)
    - autres aliments : saccharose (sucre ajouté le plus courant), sinon sucres totaux
      pour les produits sucrés et glaces.
    """
    if ssgrp in {"0201", "0202", "0203", "0204"} or grp == "04":
        return 0.0
    if grp == "06" or ssgrp in {"0701", "0704"}:
        return sucres or 0.0
    if saccharose is not None:
        return saccharose
    if grp in {"07", "08"}:
        return sucres or 0.0
    return 0.0


def convertir(chemin_xlsx: str | Path) -> pd.DataFrame:
    brut = pd.read_excel(chemin_xlsx, dtype=str)
    entetes = {nettoyer(c): c for c in brut.columns}
    colonnes = {}
    for cle, motif in MOTIFS.items():
        trouve = [orig for propre, orig in entetes.items() if re.search(motif, propre)]
        if not trouve:
            raise ValueError(f"Colonne introuvable pour « {cle} » (motif {motif})")
        colonnes[cle] = trouve[0]

    lignes = []
    for _, r in brut.iterrows():
        grp = nettoyer(r["alim_grp_code"]).zfill(2)
        ssgrp = nettoyer(r["alim_ssgrp_code"]).zfill(4)
        kcal = nombre(r[colonnes["kcal"]])
        nom = nettoyer(r["alim_nom_fr"])
        if not nom or kcal is None or grp in {"00", "11"}:  # aliments moyens et infantiles exclus
            continue
        v = {k: nombre(r[c]) for k, c in colonnes.items()}
        lignes.append({
            "code": int(float(r["alim_code"])),
            "nom": nom,
            "categorie": categorie(grp, ssgrp),
            "groupe_ciqual": nettoyer(r["alim_ssgrp_nom_fr"]) or nettoyer(r["alim_grp_nom_fr"]),
            "kcal": round(kcal, 1),
            "proteines": round(v["proteines"] or 0, 2),
            "glucides": round(v["glucides"] or 0, 2),
            "lipides": round(v["lipides"] or 0, 2),
            "fibres": round(v["fibres"] or 0, 2),
            "sucres_libres": round(sucres_libres(grp, ssgrp, v["sucres"], v["saccharose"]), 2),
            "sel": round(v["sel"] or 0, 3),
        })
    return pd.DataFrame(lignes).sort_values("nom").reset_index(drop=True)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    df = convertir(argv[1])
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"{len(df)} aliments écrits dans {SORTIE}")
    print(df["categorie"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
