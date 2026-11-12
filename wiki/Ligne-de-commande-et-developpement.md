[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Command-line-and-development)

## Ligne de commande

Avec le `.exe`, remplace `python -m entity_toolkit` par `EntityToolkit.exe` (il n'a pas de console : regarde `data\entity_toolkit.log` pour voir ce qu'il a fait).

```text
python -m entity_toolkit                  démarrer (comme run.bat)
python -m entity_toolkit update-db        télécharger / rafraîchir les données  [--only patch builds perks loadout maps nl_maps] [--refresh]
python -m entity_toolkit login            se connecter à NightLight
python -m entity_toolkit autostart install   démarrer tout seul avec le jeu (autostart remove pour annuler)
python -m entity_toolkit test-image X.jpg analyser une capture comme si tu avais appuyé sur ta touche de capture dessus (simulation)
python -m entity_toolkit serve --demo     servir les pages avec un résultat inventé, sans le jeu
```

## Développement

```bash
python -m unittest discover -s tests
```

| Module | Rôle |
|---|---|
| `assistant.py` | La touche de capture, et quoi faire sur chaque écran (menu des joueurs, tableau de fin) |
| `auto.py` | Mode automatique : voir le menu des joueurs et le tableau de fin terminé sans touche |
| `recognize.py`, `analyzer.py` | Perks, noms et map d'après une capture du menu des joueurs |
| `overlay.py` | La fenêtre transparente et l'association allié → ligne |
| `nightlight.py`, `review.py` | Envoi, mémoire de la map, revue automatique |
| `levels.py` | Niveaux, historique, sauvegardes, lecture de la pastille du tableau de fin |
| `perk_types.py`, `mybuilds.py` | Création de build : ce que fait un perk (plusieurs types par perk), builds enregistrés |
| `shrine.py`, `version.py`, `tray.py` | Le Shrine de la semaine, la vérification de version, l'icône de la zone de notification |
| `database/seed.py`, `seed/` | La base de données livrée avec l'outil, et son installation au premier démarrage |
| `packaging/` | Le `.exe` : recette PyInstaller et `build.py` (zip + SHA-256) |
| `database/` | `update-db` : téléchargements du wiki, d'Otzdarva et de NightLight, ce qui a changé (`changes.py`), rafraîchissement automatique |
| `server.py`, `web/` | Pages locales et API JSON |
| `window.py` | La fenêtre Entity Toolkit (pywebview / WebView2) qui affiche ces pages, et son lanceur |

**Publier une version.** Rafraîchis la base livrée (`Update database`, puis `python packaging/make_seed.py`). Change `__version__` dans `entity_toolkit/__init__.py`, commite, puis pousse un tag du même numéro (`git tag v0.3.0`, `git push origin v0.3.0`). Le [workflow de release](https://github.com/Tau-hub/entity-toolkit/blob/main/.github/workflows/release.yml) lance les tests, construit le `.exe` sur une machine Windows propre, l'atteste et crée une release en **brouillon** avec le zip, `SHA256SUMS.txt` et les notes d'installation : relis-la, puis clique sur *Publish*. Le mode d'emploi est dans le dossier `wiki/` : après une modification, `python packaging/publish_wiki.py` le copie vers le wiki. Pour construire en local : `pip install pyinstaller`, puis `python packaging/build.py` (résultat dans `dist/`).

Contributions : ouvre d'abord une issue pour tout ce qui est gros (voir aussi [Assistance de l'IA](https://github.com/Tau-hub/entity-toolkit/blob/main/README.fr.md#assistance-de-lia)).
