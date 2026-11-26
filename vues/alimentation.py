from datetime import timedelta

import streamlit as st

from nutrima import aliments as base
from nutrima import db, ui
from nutrima.calculs import aliment_manuel, nouvel_aliment
from nutrima.referentiels import REPAS

u, j = ui.uid(), ui.jour()

st.title(f"🍽️ Alimentation du {j.strftime('%d/%m/%Y')}")

repas = st.segmented_control("Repas", REPAS, default=REPAS[1], key="repas_choisi") or REPAS[1]


def ajouter(f: dict) -> None:
    db.ajouter_aliment(u, j, repas, f)
    st.toast(f"{f['aliment']} ajouté au {repas.lower()}.", icon="✅")


t_rech, t_rec, t_man, t_cop = st.tabs(["🔎 Rechercher", "🕘 Récents", "✏️ Saisie manuelle", "📋 Copier un repas"])

# ----- Recherche dans Ciqual
with t_rech:
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("Aliment", placeholder="ex. pomme crue, pain complet, yaourt nature…", key="q_alim")
    cat = c2.selectbox("Catégorie", ["Toutes"] + base.categories(), key="cat_alim")
    res = base.rechercher(q, None if cat == "Toutes" else cat, limite=60)
    if res.empty:
        st.warning("Aucun aliment trouvé. Essaie un autre mot, ou utilise la saisie manuelle.")
    else:
        code = st.selectbox(f"Résultats ({len(res)}{'+' if len(res) == 60 else ''})", res["code"].tolist(),
                            format_func=lambda c: res.loc[res["code"] == c, "nom"].iloc[0], key="code_alim")
        al = base.par_code(code)
        c1, c2 = st.columns([1, 2])
        g = c1.number_input("Quantité (g ou ml)", 1, 2000, 100, 10, key="g_alim")
        f = nouvel_aliment(al["nom"], g, al.to_dict(), al["categorie"], int(al["code"]))
        c2.markdown(
            f"**{f['kcal']:.0f} kcal** · protéines {f['proteines']:.1f} g · glucides {f['glucides']:.1f} g · "
            f"lipides {f['lipides']:.1f} g · fibres {f['fibres']:.1f} g · sel {f['sel']:.2f} g  \n"
            f"<small>{al['categorie']} · pour 100 g : {al['kcal']:.0f} kcal</small>", unsafe_allow_html=True)
        if st.button("➕ Ajouter", type="primary", key="add_rech"):
            ajouter(f)
            st.rerun()
    st.caption("Source : table Ciqual 2025 (ANSES). Les sucres libres sont estimés.")

# ----- Aliments récents
with t_rec:
    rec = db.aliments_recents(u)
    if not rec:
        st.caption("Les aliments que tu ajoutes depuis la recherche apparaîtront ici.")
    for i, r in enumerate(rec):
        al = base.par_code(r["code"])
        if al is None:
            continue
        c1, c2, c3 = st.columns([4, 1.2, 1])
        c1.markdown(f"{r['aliment']}")
        g = c2.number_input("g", 1, 2000, int(r["quantite_g"]), 10, key=f"rec_g_{r['code']}",
                            label_visibility="collapsed")
        if c3.button("➕", key=f"rec_add_{r['code']}", width="stretch"):
            ajouter(nouvel_aliment(al["nom"], g, al.to_dict(), al["categorie"], int(al["code"])))
            st.rerun()

# ----- Saisie manuelle
with t_man:
    with st.form("f_manuel", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        nom = c1.text_input("Nom du plat", "Plat maison", max_chars=80)
        g = c2.number_input("Quantité (g)", 1, 3000, 300, 10)
        st.caption("Valeurs pour la portion entière (regarde l'étiquette ou une recette).")
        m = st.columns(4)
        kcal = m[0].number_input("kcal", 0, 5000, 400)
        prot = m[1].number_input("Protéines (g)", 0.0, 300.0, 20.0)
        gluc = m[2].number_input("Glucides (g)", 0.0, 500.0, 40.0)
        lip = m[3].number_input("Lipides (g)", 0.0, 300.0, 15.0)
        m = st.columns(4)
        fib = m[0].number_input("Fibres (g)", 0.0, 100.0, 4.0)
        su = m[1].number_input("Sucres ajoutés (g)", 0.0, 300.0, 5.0)
        sel = m[2].number_input("Sel (g)", 0.0, 30.0, 1.0)
        fl = m[3].number_input("Portions fruits/légumes", 0.0, 10.0, 0.0, 0.5, help="1 portion ≈ 80 g")
        if st.form_submit_button("➕ Ajouter le plat", type="primary"):
            ajouter(aliment_manuel(nom, g, dict(kcal=kcal, proteines=prot, glucides=gluc, lipides=lip, fibres=fib,
                                                sucres_libres=su, sel=sel, portions_fl=fl)))

# ----- Copier
with t_cop:
    c1, c2 = st.columns(2)
    src = c1.date_input("Copier depuis le", j - timedelta(days=1), max_value=j, format="DD/MM/YYYY", key="cop_d")
    quoi = c2.selectbox("Quoi", ["Toute la journée"] + REPAS, key="cop_r")
    apercu = db.aliments(u, src, src)
    if quoi != "Toute la journée":
        apercu = apercu[apercu["repas"] == quoi]
    if apercu.empty:
        st.caption("Rien à copier pour cette sélection.")
    else:
        st.caption(", ".join(apercu["aliment"].head(12)) + ("…" if len(apercu) > 12 else ""))
        if st.button(f"📋 Copier {len(apercu)} aliment(s) vers le {j.strftime('%d/%m')}", disabled=src == j):
            n = db.copier_repas(u, src, j, None if quoi == "Toute la journée" else quoi)
            st.toast(f"{n} aliment(s) copiés.", icon="✅")
            st.rerun()

# ---------------------------------------------------------------------------
st.divider()
f = db.aliments(u, j, j)
if f.empty:
    st.caption("Aucun aliment saisi pour ce jour.")
else:
    c = st.columns(5)
    c[0].metric("Énergie", f"{f['kcal'].sum():.0f} kcal")
    c[1].metric("Protéines", f"{f['proteines'].sum():.0f} g")
    c[2].metric("Fibres", f"{f['fibres'].sum():.0f} g")
    c[3].metric("Fruits & légumes", f"{f['portions_fl'].sum():.1f} / 5")
    c[4].metric("Sel", f"{f['sel'].sum():.1f} g")

    f["_ordre"] = f["repas"].map({r: i for i, r in enumerate(REPAS)})
    f = f.sort_values(["_ordre", "id"])
    vue = ui.renommer_aliments(f[["repas", "aliment", "quantite_g", "kcal", "proteines", "glucides",
                                  "lipides", "fibres", "sel"]])
    ev = st.dataframe(vue, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row",
                      key=f"tab_food_{st.session_state.get('v_food', 0)}", column_config={"kcal": st.column_config.NumberColumn(format="%.0f")})
    sel = ev.selection.rows
    if st.button(f"🗑️ Supprimer la sélection ({len(sel)})", disabled=not sel):
        db.supprimer_lignes("repas", u, f.iloc[sel]["id"].tolist())
        st.session_state.v_food = st.session_state.get("v_food", 0) + 1  # réinitialise la sélection
        st.rerun()
