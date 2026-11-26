# 🥗 Nutrima

**Bouger plus, mieux manger, à tout âge.** Nutrima est une application web (Streamlit) de suivi de l'activité
physique, de la sédentarité et de l'alimentation, avec un score santé et des conseils adaptés à l'âge
(enfants, adultes, seniors). Projet GEII lié à l'**ODD 3 : bonne santé et bien-être**.

## Fonctionnalités

- **Comptes** : identifiant et mot de passe (haché avec bcrypt), chaque compte ne voit que ses données.
- **Profil sauvegardé** : date de naissance (l'âge se met à jour tout seul), taille, objectif et suivi du poids.
- **Activité** : 22 activités avec leurs valeurs MET, temps assis du jour.
- **Alimentation** : plus de 3 300 aliments de la **table Ciqual 2025 (ANSES)**, recherche sans accents,
  aliments récents, saisie manuelle, copie d'un repas d'un autre jour.
- **Aujourd'hui** : score santé sur 100, objectifs sur 7 jours, série de jours, conseils personnalisés
  (activité, renforcement, équilibre, sédentarité, écrans, énergie, fruits et légumes, fibres, sucres, sel,
  protéines…).
- **Tendances** : score, activité, énergie, poids et temps assis sur 7, 30 ou 90 jours.
- **Mes données** : export CSV, changement de mot de passe, effacement du suivi, suppression du compte.

## Installation

Python 3.10 ou plus récent.

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501. Pour la rendre accessible aux autres postes du réseau :

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Compte de démonstration (pour une présentation)

```bash
python scripts/creer_demo.py
```

Crée le compte `demo` / `demo1234` avec 30 jours de données. **Ne pas lancer sur le serveur de production.**

## Données et sauvegarde

- Les données sont dans une base **SQLite** : `data/nutrima.db` par défaut.
  On peut changer son emplacement avec la variable d'environnement `NUTRIMA_DB`.
- La base est exclue de git (`.gitignore`) : elle contient les comptes des utilisateurs.
- **Sauvegarde** : copier régulièrement le fichier `nutrima.db` (par exemple une tâche planifiée chaque nuit).
- En production, placer l'application derrière un **reverse proxy HTTPS** (Caddy, nginx) pour que les mots
  de passe ne circulent pas en clair sur le réseau.
- La connexion dure le temps de l'onglet : recharger la page demande de se reconnecter.

## Mettre à jour la base d'aliments

`data/aliments_ciqual.csv` est généré depuis le fichier Excel officiel de Ciqual :

```bash
pip install -r requirements-dev.txt
python scripts/import_ciqual.py "Table Ciqual 2025_FR_2025_11_03.xlsx"
```

Source : ANSES, *Table de composition nutritionnelle des aliments Ciqual 2025*,
[doi:10.57745/RDMHWY](https://doi.org/10.57745/RDMHWY), licence Etalab 2.0.
Les **sucres libres** (repère OMS) ne figurent pas dans Ciqual : le script les estime (voir `sucres_libres()`).

## Organisation du code

```
app.py                 point d'entrée : connexion et navigation
nutrima/
  calculs.py           profil, besoins énergétiques, bilan et score (sans Streamlit, testé)
  conseils.py          conseils personnalisés selon l'âge et le bilan
  referentiels.py      activités (MET), repas, objectifs
  aliments.py          table Ciqual et recherche
  db.py                stockage SQLite
  auth.py              comptes et mots de passe
  ui.py                éléments d'interface partagés
vues/                  une page Streamlit par fichier
scripts/               import Ciqual, compte de démo
tests/                 tests pytest
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Limites

Les résultats sont des estimations fondées sur des valeurs moyennes. Ils **ne remplacent pas l'avis d'un
médecin ou d'un diététicien**.
