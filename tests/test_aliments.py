from nutrima import aliments as base


def test_table_chargee():
    t = base.table()
    assert len(t) > 3000
    assert {"code", "nom", "categorie", "kcal", "sel", "sucres_libres"} <= set(t.columns)
    assert t["code"].is_unique


def test_recherche_sans_accents_et_mots_dans_le_desordre():
    res = base.rechercher("creme brulee")
    assert any("Crème brûlée" in n for n in res["nom"])
    res = base.rechercher("crue pomme")
    assert "Pomme, chair et peau, crue" in res["nom"].tolist()


def test_recherche_priorise_le_debut_du_nom():
    res = base.rechercher("pomme")
    assert res.iloc[0]["nom"].lower().startswith("pomme")


def test_recherche_par_categorie():
    res = base.rechercher("", "Boissons", limite=500)
    assert set(res["categorie"]) == {"Boissons"}


def test_sucres_libres_estimes():
    pomme = base.par_code(13039)
    cola = base.par_code(18018)
    assert pomme["sucres_libres"] == 0      # sucres naturels du fruit
    assert cola["sucres_libres"] > 8        # soda : sucres libres
    assert base.par_code(99999999) is None
