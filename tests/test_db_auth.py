from datetime import date, timedelta

import pytest

from nutrima import auth
from nutrima.calculs import nouvel_aliment, nouvelle_activite

J = date(2026, 11, 26)


def test_inscription_et_connexion(base_temp):
    uid = auth.inscrire("Alice", "motdepasse1", "motdepasse1")
    assert auth.connecter("alice", "motdepasse1") == uid  # identifiant insensible à la casse
    with pytest.raises(auth.ErreurAuth):
        auth.connecter("alice", "mauvais123")
    with pytest.raises(auth.ErreurAuth):
        auth.connecter("inconnu", "motdepasse1")


def test_mot_de_passe_jamais_en_clair(base_temp):
    auth.inscrire("bob", "secret1234", "secret1234")
    u = base_temp.utilisateur_par_nom("bob")
    assert "secret1234" not in u["pw_hash"]
    assert u["pw_hash"].startswith("$2")


@pytest.mark.parametrize("nom,mdp,conf", [
    ("ab", "motdepasse1", "motdepasse1"),        # identifiant trop court
    ("nom avec espace", "motdepasse1", "motdepasse1"),
    ("carla", "court1", "court1"),               # mot de passe trop court
    ("carla", "seulementdeslettres", "seulementdeslettres"),
    ("carla", "motdepasse1", "motdepasse2"),     # confirmation différente
])
def test_inscription_refusee(base_temp, nom, mdp, conf):
    with pytest.raises(auth.ErreurAuth):
        auth.inscrire(nom, mdp, conf)


def test_identifiant_unique(base_temp):
    auth.inscrire("dan", "motdepasse1", "motdepasse1")
    with pytest.raises(auth.ErreurAuth, match="déjà pris"):
        auth.inscrire("DAN", "motdepasse1", "motdepasse1")


def test_changer_mdp(base_temp):
    uid = auth.inscrire("eve", "motdepasse1", "motdepasse1")
    auth.changer_mdp(uid, "eve", "motdepasse1", "nouveau2024", "nouveau2024")
    assert auth.connecter("eve", "nouveau2024") == uid


def test_profil_et_poids_historique(base_temp):
    db = base_temp
    uid = auth.inscrire("fred", "motdepasse1", "motdepasse1")
    assert db.charger_profil(uid) is None
    db.enregistrer_profil(uid, "Fred", date(1980, 1, 1), "Homme", 180, "Maintenir mon poids")
    db.enregistrer_poids(uid, J - timedelta(days=10), 82)
    db.enregistrer_poids(uid, J, 80)
    assert db.charger_profil(uid, J - timedelta(days=5)).poids == 82
    assert db.charger_profil(uid, J).poids == 80
    assert db.charger_profil(uid, J - timedelta(days=30)).poids == 82  # avant la 1re pesée


def test_isolation_entre_comptes(base_temp):
    db = base_temp
    a = auth.inscrire("anna", "motdepasse1", "motdepasse1")
    b = auth.inscrire("ben", "motdepasse1", "motdepasse1")
    db.ajouter_activite(a, J, nouvelle_activite("Natation", 30, 60))
    assert len(db.activites(a)) == 1
    assert len(db.activites(b)) == 0
    # b ne peut pas supprimer une ligne de a
    db.supprimer_lignes("activites", b, db.activites(a)["id"].tolist())
    assert len(db.activites(a)) == 1


def test_repas_copie_recents_et_suppression_compte(base_temp):
    db = base_temp
    uid = auth.inscrire("gina", "motdepasse1", "motdepasse1")
    f = nouvel_aliment("Pomme", 150, {"kcal": 54}, "Fruits & légumes", 13039)
    db.ajouter_aliment(uid, J - timedelta(days=1), "Collation", f)
    db.ajouter_aliment(uid, J - timedelta(days=1), "Dîner", nouvel_aliment("Pain", 50, {"kcal": 276}, "Autres", 7000))
    assert db.copier_repas(uid, J - timedelta(days=1), J, "Collation") == 1
    assert db.aliments(uid, J, J)["aliment"].tolist() == ["Pomme"]
    assert {r["code"] for r in db.aliments_recents(uid)} == {13039, 7000}
    db.enregistrer_assis(uid, J, 7)
    assert db.assis(uid, J, J) == {J: 7.0}
    assert db.jours_avec_saisie(uid) == {J, J - timedelta(days=1)}
    db.supprimer_utilisateur(uid)
    assert db.aliments(uid).empty  # suppression en cascade
    assert db.assis(uid) == {}
