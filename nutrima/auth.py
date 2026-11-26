"""Comptes utilisateurs : mots de passe hachés avec bcrypt, jamais stockés en clair."""
from __future__ import annotations

import re
import sqlite3

import bcrypt

from . import db

RE_NOM = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
MDP_MIN = 8


class ErreurAuth(ValueError):
    pass


def hacher(mdp: str) -> str:
    # bcrypt ne prend en compte que 72 octets : on refuse au-delà plutôt que de tronquer en silence
    return bcrypt.hashpw(mdp.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verifier(mdp: str, pw_hash: str) -> bool:
    try:
        return bcrypt.checkpw(mdp.encode("utf-8"), pw_hash.encode("ascii"))
    except ValueError:
        return False


def valider_mdp(mdp: str) -> None:
    if len(mdp) < MDP_MIN:
        raise ErreurAuth(f"Le mot de passe doit contenir au moins {MDP_MIN} caractères.")
    if len(mdp.encode("utf-8")) > 72:
        raise ErreurAuth("Le mot de passe est trop long (72 octets maximum).")
    if mdp.isdigit() or mdp.isalpha():
        raise ErreurAuth("Le mot de passe doit mélanger lettres et chiffres (ou symboles).")


def inscrire(username: str, mdp: str, confirmation: str) -> int:
    username = username.strip()
    if not RE_NOM.match(username):
        raise ErreurAuth("Identifiant : 3 à 30 caractères, lettres, chiffres, « . », « _ » ou « - ».")
    if mdp != confirmation:
        raise ErreurAuth("Les deux mots de passe ne correspondent pas.")
    valider_mdp(mdp)
    try:
        return db.creer_utilisateur(username, hacher(mdp))
    except sqlite3.IntegrityError:
        raise ErreurAuth("Cet identifiant est déjà pris.") from None


# Hash factice pour que la durée de vérification soit la même que l'utilisateur existe ou non
_HASH_FACTICE = hacher("nutrima-hash-factice-0")


def connecter(username: str, mdp: str) -> int:
    u = db.utilisateur_par_nom(username.strip())
    if u is None:
        verifier(mdp, _HASH_FACTICE)
        raise ErreurAuth("Identifiant ou mot de passe incorrect.")
    if not verifier(mdp, u["pw_hash"]):
        raise ErreurAuth("Identifiant ou mot de passe incorrect.")
    return int(u["id"])


def changer_mdp(user_id: int, username: str, ancien: str, nouveau: str, confirmation: str) -> None:
    connecter(username, ancien)
    if nouveau != confirmation:
        raise ErreurAuth("Les deux nouveaux mots de passe ne correspondent pas.")
    valider_mdp(nouveau)
    db.changer_mot_de_passe(user_id, hacher(nouveau))
