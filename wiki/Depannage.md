[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Troubleshooting)

## Dépannage

`data/entity_toolkit.log` dit ce que l'outil a vu et fait, avec l'heure : c'est le premier endroit où regarder. Les captures qu'il a lues sont dans `data/captures/`.

### Rien ne se passe

- Le jeu doit être lancé **et** être la fenêtre au premier plan, en mode fenêtré ou fenêtré sans bordure, en anglais.
- L'outil doit tourner : le **E** rouge est dans la zone de notification.
- **Mode Hotkey :** appuie sur la touche de capture réglée dans Settings (Alt + pavé numérique 7 tant que tu ne la changes pas). Une touche du pavé numérique demande le verrouillage numérique. Un nouveau raccourci ne prend effet qu'après un redémarrage de l'outil.
- **Mode automatique :** vérifie que Settings indique *Automatic*, et garde le menu des joueurs ouvert environ une seconde. Après un appui de moins d'une demi-seconde, le journal indique *« Tab pressed but the players menu was not seen »* : refais Tab un peu plus longtemps.

### La fenêtre ne s'ouvre pas, ou je l'ai fermée

- Fermée avec *Keep it running* : double-clique sur le **E** rouge dans la zone de notification, ou relance le programme.
- Si la fenêtre ne peut pas démarrer (le moteur WebView2 manque sur un vieux Windows 10), l'outil ouvre ton navigateur à la place et le dit dans le journal. Installe le *WebView2 Runtime* de Microsoft, ou décoche *Show the pages in the Entity Toolkit window* dans Settings.
- Elle s'est ouverte hors de l'écran après le débranchement d'un moniteur : elle revient au milieu d'un écran au prochain démarrage.

### « Screen not recognised » (mode Hotkey)

L'outil cherche les mots *PLAYERS / QUESTS* (menu des joueurs) ou *MATCH SCOREBOARD* en haut à gauche. Vérifie que le jeu est en anglais et que tu as appuyé sur ta touche de capture sur l'un de ces deux écrans. La capture est gardée dans `data/debug/` (`*_unknown.jpg`). En mode automatique, ça ne peut pas arriver : un autre écran est simplement ignoré.

### Un allié ou une perk manque, ou est faux

- La souris était sur un objet ou une perk quand le menu a été lu : l'infobulle du jeu en cachait une partie. L'outil assemble plusieurs captures pour contourner ça ; si ça ne suffit pas, rouvre le menu avec la souris loin des icônes (et appuie sur ta touche de capture en mode Hotkey).
- Les perks sous 78 % de confiance sont marquées « to check » sur la page Live.
- Après un patch du jeu, lance **Update database** pour que les nouvelles icônes existent.

### Les perks sont restées après la partie, ou ont disparu pendant

- Elles sont retirées quand le tableau de fin est lu. Si tu as quitté la partie sans voir le tableau (ou sans appuyer sur ta touche de capture dessus, en mode Hotkey), elles restent jusqu'à la prochaine lecture du menu des joueurs, ou jusqu'à ta touche qui retire l'overlay.
- Elles disparaissent si l'outil est redémarré pendant une partie : relis le menu des joueurs.

### Mode automatique : le tableau de fin ne part pas

- L'outil attend que les quatre survivants et le tueur affichent tous leurs perks : tant qu'une ligne est cachée, la partie n'est pas finie. La page Live indique alors *« waiting for the end of the match »*.
- Un match personnalisé avec moins de joueurs, ou un joueur venu sans aucune perk, ne remplit jamais cette condition : appuie sur ta touche de capture sur le tableau.
- NightLight doit être configuré (un jeton, et une connexion). Sans ça, rien n'est envoyé et rien n'est signalé : c'est voulu.

### Overlay mal placé

Les positions sont proportionnelles à la hauteur de l'écran du jeu et ont été mesurées en 2560×1440. Ajuste `data/overlay_layout.json` (`x`, `dy`, `rows`, `size`, `gap`, décrits en tête de `entity_toolkit/overlay.py`) et relis le menu des joueurs. Les pull requests avec des mesures pour d'autres résolutions sont les bienvenues.

### La revue NightLight échoue

Edge doit être installé et tu dois t'être connecté une fois (Settings → Sign in to NightLight). La fenêtre est visible exprès : NightLight est derrière Cloudflare, qui refuse les navigateurs invisibles. L'outil rend le focus au jeu pendant qu'il travaille.

### Les noms de la liste du jeu sont illisibles

Windows ne lit que les alphabets des modules linguistiques installés (un pseudo en cyrillique n'est pas lu avec un module anglais). L'overlay place alors les alliés d'après leur portrait, et se rabat sur l'ordre du menu quand deux d'entre eux jouent le même personnage.
