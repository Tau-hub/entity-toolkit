[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Troubleshooting)

## Dépannage

- **« Screen not recognised »** : l'outil cherche les mots *PLAYERS / QUESTS* (menu des joueurs) ou *MATCH SCOREBOARD* en haut à gauche. Vérifie que le jeu est en anglais et que tu as appuyé sur l'un de ces deux écrans. La capture est gardée dans `data/debug/` (`*_unknown.jpg`).
- **Rien ne se passe** : le jeu doit être lancé et au premier plan. Regarde `data/entity_toolkit.log`. Lance `python -m entity_toolkit` à la place de `run.bat` pour voir la console.
- **Perks faux ou manquants** : les perks sous 78 % de confiance sont marqués « to check » sur la page Live. Lance **Update database** après un patch pour que les nouvelles icônes existent.
- **Overlay mal placé** : les positions sont proportionnelles à la hauteur de l'écran du jeu et ont été mesurées en 2560×1440. Ajuste `data/overlay_layout.json` (`x`, `dy`, `rows`, `size`, `gap`, décrits en tête de `entity_toolkit/overlay.py`) et rappuie sur la touche. Les pull requests avec des mesures pour d'autres résolutions sont très bienvenues.
- **La revue NightLight échoue** : Edge doit être installé et tu dois t'être connecté une fois (Settings → Sign in to NightLight). La fenêtre est visible exprès : NightLight est derrière Cloudflare, qui refuse les navigateurs invisibles. L'outil rend le focus au jeu pendant qu'il travaille.
- **Les noms de la liste du jeu sont illisibles** : l'overlay se rabat alors sur l'ordre du menu.
