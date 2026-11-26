"""Base d'aliments Ciqual (ANSES) : chargement et recherche insensible aux accents."""
from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "aliments_ciqual.csv"


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFKD", str(texte).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("œ", "oe").replace("æ", "ae")


@lru_cache(maxsize=1)
def table(chemin: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(chemin or CSV, encoding="utf-8")
    df["_cle"] = df["nom"].map(normaliser)
    # Les aliments « bruts » d'abord (noms courts), les plats préemballés ensuite
    df["_rang"] = df["nom"].str.len()
    return df


def rechercher(requete: str, categorie: str | None = None, limite: int = 50,
               df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Chaque mot de la requête doit apparaître dans le nom (ordre libre, sans accents)."""
    df = table() if df is None else df
    if categorie:
        df = df[df["categorie"] == categorie]
    mots = normaliser(requete).split()
    if not mots:
        return df.sort_values("_rang").head(limite)
    masque = pd.Series(True, index=df.index)
    for m in mots:
        masque &= df["_cle"].str.contains(m, regex=False)
    res = df[masque].copy()
    # Bonus si le nom commence par le premier mot recherché
    res["_score"] = res["_rang"] - 1000 * res["_cle"].str.startswith(mots[0])
    return res.sort_values("_score").head(limite)


def par_code(code: int, df: pd.DataFrame | None = None) -> pd.Series | None:
    df = table() if df is None else df
    r = df[df["code"] == int(code)]
    return None if r.empty else r.iloc[0]


def categories(df: pd.DataFrame | None = None) -> list[str]:
    df = table() if df is None else df
    return sorted(df["categorie"].unique())
