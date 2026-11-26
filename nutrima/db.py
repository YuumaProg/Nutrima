"""Stockage SQLite. Chaque requête filtre par user_id : un compte ne voit que ses données.

Le chemin de la base se règle avec la variable d'environnement NUTRIMA_DB
(par défaut : data/nutrima.db à la racine du projet).
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .calculs import ACT_COLS, FOOD_COLS, Profil

RACINE = Path(__file__).resolve().parent.parent
DB_DEFAUT = RACINE / "data" / "nutrima.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE COLLATE NOCASE,
    pw_hash     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profils (
    user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    prenom      TEXT NOT NULL DEFAULT '',
    naissance   TEXT NOT NULL,
    sexe        TEXT NOT NULL,
    taille      REAL NOT NULL,
    objectif    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS poids (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,
    kg          REAL NOT NULL,
    PRIMARY KEY (user_id, date)
);
CREATE TABLE IF NOT EXISTS activites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,
    nom         TEXT NOT NULL,
    duree       INTEGER NOT NULL,
    intensite   TEXT NOT NULL,
    kcal        REAL NOT NULL,
    tag         TEXT
);
CREATE INDEX IF NOT EXISTS idx_act_user_date ON activites(user_id, date);
CREATE TABLE IF NOT EXISTS repas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,
    repas       TEXT NOT NULL,
    aliment     TEXT NOT NULL,
    code        INTEGER,
    quantite_g  REAL NOT NULL,
    categorie   TEXT NOT NULL,
    kcal        REAL NOT NULL,
    proteines   REAL NOT NULL,
    glucides    REAL NOT NULL,
    lipides     REAL NOT NULL,
    fibres      REAL NOT NULL,
    sucres_libres REAL NOT NULL,
    sel         REAL NOT NULL,
    portions_fl REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repas_user_date ON repas(user_id, date);
CREATE TABLE IF NOT EXISTS assis (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,
    heures      REAL NOT NULL,
    PRIMARY KEY (user_id, date)
);
"""


def chemin_db() -> Path:
    return Path(os.environ.get("NUTRIMA_DB", DB_DEFAUT))


@contextmanager
def connexion(chemin: Path | str | None = None):
    p = Path(chemin) if chemin else chemin_db()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, detect_types=0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db(chemin: Path | str | None = None) -> None:
    with connexion(chemin) as con:
        con.executescript(SCHEMA)
        con.execute("PRAGMA journal_mode = WAL")


def _d(x: date) -> str:
    return x.isoformat()


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------
def creer_utilisateur(username: str, pw_hash: str) -> int:
    with connexion() as con:
        cur = con.execute("INSERT INTO users(username, pw_hash, created_at) VALUES (?, ?, ?)",
                          (username, pw_hash, datetime.now().isoformat(timespec="seconds")))
        return int(cur.lastrowid)


def utilisateur_par_nom(username: str) -> sqlite3.Row | None:
    with connexion() as con:
        return con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def changer_mot_de_passe(user_id: int, pw_hash: str) -> None:
    with connexion() as con:
        con.execute("UPDATE users SET pw_hash = ? WHERE id = ?", (pw_hash, user_id))


def supprimer_utilisateur(user_id: int) -> None:
    with connexion() as con:
        con.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ---------------------------------------------------------------------------
# Profil et poids
# ---------------------------------------------------------------------------
def enregistrer_profil(user_id: int, prenom: str, naissance: date, sexe: str, taille: float,
                       objectif: str) -> None:
    with connexion() as con:
        con.execute(
            """INSERT INTO profils(user_id, prenom, naissance, sexe, taille, objectif)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET prenom=excluded.prenom, naissance=excluded.naissance,
                 sexe=excluded.sexe, taille=excluded.taille, objectif=excluded.objectif""",
            (user_id, prenom.strip(), _d(naissance), sexe, float(taille), objectif))


def enregistrer_poids(user_id: int, jour: date, kg: float) -> None:
    with connexion() as con:
        con.execute("""INSERT INTO poids(user_id, date, kg) VALUES (?, ?, ?)
                       ON CONFLICT(user_id, date) DO UPDATE SET kg = excluded.kg""",
                    (user_id, _d(jour), float(kg)))


def poids_au(user_id: int, jour: date) -> float | None:
    """Dernier poids connu à cette date (ou le premier enregistré s'il n'y en a pas avant)."""
    with connexion() as con:
        r = con.execute("SELECT kg FROM poids WHERE user_id = ? AND date <= ? ORDER BY date DESC LIMIT 1",
                        (user_id, _d(jour))).fetchone()
        if r is None:
            r = con.execute("SELECT kg FROM poids WHERE user_id = ? ORDER BY date LIMIT 1",
                            (user_id,)).fetchone()
        return float(r["kg"]) if r else None


def historique_poids(user_id: int) -> pd.DataFrame:
    with connexion() as con:
        df = pd.read_sql_query("SELECT date, kg FROM poids WHERE user_id = ? ORDER BY date", con,
                               params=(user_id,))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def supprimer_poids(user_id: int, jour: date) -> None:
    with connexion() as con:
        con.execute("DELETE FROM poids WHERE user_id = ? AND date = ?", (user_id, _d(jour)))


def charger_profil(user_id: int, jour: date | None = None) -> Profil | None:
    with connexion() as con:
        r = con.execute("SELECT * FROM profils WHERE user_id = ?", (user_id,)).fetchone()
    if r is None:
        return None
    kg = poids_au(user_id, jour or date.today())
    if kg is None:
        return None
    return Profil(naissance=date.fromisoformat(r["naissance"]), sexe=r["sexe"], taille=r["taille"],
                  poids=kg, objectif=r["objectif"], prenom=r["prenom"])


# ---------------------------------------------------------------------------
# Activités, repas, temps assis
# ---------------------------------------------------------------------------
def ajouter_activite(user_id: int, jour: date, a: dict) -> None:
    with connexion() as con:
        con.execute("""INSERT INTO activites(user_id, date, nom, duree, intensite, kcal, tag)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, _d(jour), a["nom"], a["duree"], a["intensite"], a["kcal"], a["tag"]))


def ajouter_aliment(user_id: int, jour: date, repas: str, f: dict) -> None:
    cols = ["aliment", "code", "quantite_g", "categorie", "kcal", "proteines", "glucides",
            "lipides", "fibres", "sucres_libres", "sel", "portions_fl"]
    with connexion() as con:
        con.execute(f"INSERT INTO repas(user_id, date, repas, {', '.join(cols)}) "
                    f"VALUES (?, ?, ?, {', '.join('?' * len(cols))})",
                    (user_id, _d(jour), repas, *[f[c] for c in cols]))


def supprimer_lignes(table: str, user_id: int, ids: list[int]) -> None:
    if table not in {"activites", "repas"} or not ids:
        return
    with connexion() as con:
        con.executemany(f"DELETE FROM {table} WHERE user_id = ? AND id = ?",
                        [(user_id, int(i)) for i in ids])


def copier_repas(user_id: int, depuis: date, vers: date, repas: str | None = None) -> int:
    """Copie les aliments d'un jour (ou d'un seul repas) vers un autre jour. Renvoie le nombre de lignes."""
    cols = ("repas, aliment, code, quantite_g, categorie, kcal, proteines, glucides, lipides, "
            "fibres, sucres_libres, sel, portions_fl")
    filtre, params = ("AND repas = ?", (repas,)) if repas else ("", ())
    with connexion() as con:
        cur = con.execute(f"INSERT INTO repas(user_id, date, {cols}) "
                          f"SELECT user_id, ?, {cols} FROM repas WHERE user_id = ? AND date = ? {filtre}",
                          (_d(vers), user_id, _d(depuis), *params))
        return cur.rowcount


def enregistrer_assis(user_id: int, jour: date, heures: float | None) -> None:
    with connexion() as con:
        if heures is None:
            con.execute("DELETE FROM assis WHERE user_id = ? AND date = ?", (user_id, _d(jour)))
        else:
            con.execute("""INSERT INTO assis(user_id, date, heures) VALUES (?, ?, ?)
                           ON CONFLICT(user_id, date) DO UPDATE SET heures = excluded.heures""",
                        (user_id, _d(jour), float(heures)))


def _df(sql: str, params: tuple, cols: list[str]) -> pd.DataFrame:
    with connexion() as con:
        df = pd.read_sql_query(sql, con, params=params)
    if df.empty:
        return pd.DataFrame(columns=cols)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def activites(user_id: int, debut: date | None = None, fin: date | None = None) -> pd.DataFrame:
    debut, fin = debut or date.min, fin or date.max
    return _df(f"SELECT {', '.join(ACT_COLS)} FROM activites WHERE user_id = ? AND date BETWEEN ? AND ? "
               "ORDER BY date, id", (user_id, _d(debut), _d(fin)), ACT_COLS)


def aliments(user_id: int, debut: date | None = None, fin: date | None = None) -> pd.DataFrame:
    debut, fin = debut or date.min, fin or date.max
    return _df(f"SELECT {', '.join(FOOD_COLS)} FROM repas WHERE user_id = ? AND date BETWEEN ? AND ? "
               "ORDER BY date, id", (user_id, _d(debut), _d(fin)), FOOD_COLS)


def assis(user_id: int, debut: date | None = None, fin: date | None = None) -> dict[date, float]:
    debut, fin = debut or date.min, fin or date.max
    with connexion() as con:
        rows = con.execute("SELECT date, heures FROM assis WHERE user_id = ? AND date BETWEEN ? AND ?",
                           (user_id, _d(debut), _d(fin))).fetchall()
    return {date.fromisoformat(r["date"]): float(r["heures"]) for r in rows}


def aliments_recents(user_id: int, limite: int = 15) -> list[dict]:
    """Aliments de la base Ciqual saisis récemment, avec la dernière quantité utilisée."""
    with connexion() as con:
        rows = con.execute(
            """SELECT code, aliment, quantite_g FROM repas
               WHERE id IN (SELECT MAX(id) FROM repas WHERE user_id = ? AND code IS NOT NULL GROUP BY code)
               ORDER BY id DESC LIMIT ?""", (user_id, limite)).fetchall()
    return [dict(r) for r in rows]


def jours_avec_saisie(user_id: int) -> set[date]:
    with connexion() as con:
        rows = con.execute("""SELECT date FROM activites WHERE user_id = ?
                              UNION SELECT date FROM repas WHERE user_id = ?
                              UNION SELECT date FROM assis WHERE user_id = ?""",
                           (user_id, user_id, user_id)).fetchall()
    return {date.fromisoformat(r["date"]) for r in rows}


def effacer_donnees(user_id: int) -> None:
    """Efface activités, repas et temps assis (garde le compte, le profil et le poids)."""
    with connexion() as con:
        for t in ("activites", "repas", "assis"):
            con.execute(f"DELETE FROM {t} WHERE user_id = ?", (user_id,))
