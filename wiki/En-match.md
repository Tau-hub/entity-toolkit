[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/In-a-match)

## Comment ça marche, pas à pas

Une seule touche, **Alt + pavé numérique 7** (verrouillage numérique activé), à trois moments d'une partie. Tout le reste est automatique.

**1. Dans le menu Tab : appuie sur la touche.** L'outil prend une capture du jeu, lit le nom de la map en bas, puis pour chaque allié le personnage, le pseudo et les quatre perks (icônes comparées à celles téléchargées). Un petit son « ok » confirme que ça a marché ; le résultat s'affiche aussi sur la page **Live**.

![Le menu Tab des joueurs, tel qu'il est lu quand tu appuies sur la touche (pseudos floutés)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/players-menu.jpg)

**2. Referme le menu : les perks apparaissent à côté de tes alliés.** La liste des survivants du jeu (en haut à gauche) n'est visible qu'une fois le menu fermé. L'outil la surveille, reconnaît chaque allié par son portrait (puis par son pseudo quand deux alliés jouent le même personnage) et dessine ses quatre perks en grille 2×2 à côté. Tu peux rappuyer sur la touche en jeu à tout moment : rien ne change, l'overlay reste jusqu'à la fin de la partie.

![De retour en jeu : les quatre perks de chaque allié sur la liste de gauche (pseudos floutés)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/ingame.jpg)

**3. À la fin de la partie, sur le tableau des scores : rappuie sur la touche.** L'overlay disparaît et la capture du tableau est lue : les joueurs, leurs perks, add-ons, offrandes, les points, et le badge de niveau de ton personnage (ton niveau est corrigé sur la page Niveaux).

![Le tableau de fin de partie envoyé à NightLight (pseudos et chat floutés)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/scoreboard.jpg)

**4. La partie est envoyée toute seule à NightLight.** Avec la map lue à l'étape 1, « Me » coché sur ton nom, tous les autres en Random, et confirmée, sans aucun clic de ta part. La partie apparaît ensuite dans ton historique NightLight comme n'importe quel envoi.

![Le résultat sur NightLight : map renseignée, toi coché « Me », les autres en Random (pseudos floutés)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/nightlight.jpg)

Si tu ne veux pas envoyer une partie, appuie sur **Alt + pavé numérique 8** avant le tableau (il retire l'overlay et oublie les perks), ou active *Dry run* dans Settings.

## En match

La touche par défaut est **Alt + pavé numérique 7** (verrouillage numérique activé). Elle ne réagit que si le jeu est lancé **et** au premier plan.

| Tu es sur… | Appuie une fois | Résultat |
|---|---|---|
| Le **menu des joueurs** (Tab), en survivant | oui | Map mémorisée, perks des alliés sur la page Live, overlay dessiné quand tu refermes le menu |
| Le **menu des joueurs**, en tueur | oui | Map mémorisée |
| Le jeu (menu fermé), overlay affiché | oui | L'overlay reste (seuls le tableau des scores ou Alt + pavé 8 le retirent) |
| Le jeu (menu fermé), overlay retiré | oui | Overlay remis avec les derniers perks lus |
| Le **tableau de fin** | oui | Overlay retiré, capture envoyée à NightLight, match revu et validé, niveau de ton personnage corrigé |
| Tout autre écran | oui | Son « pas ok », rien n'est envoyé |

**Alt + pavé numérique 8** retire l'overlay et oublie les perks (pratique si tu ne veux pas envoyer ce match). Les deux touches se changent dans la page Settings.

L'outil s'arrête tout seul quand le jeu se ferme. Pour qu'il démarre tout seul quand le jeu démarre : `python -m entity_toolkit autostart install` (annuler avec `autostart remove`). Une seule copie tourne à la fois : si tu le lances avec `run.bat` et que le surveillant du démarrage automatique le relance au démarrage du jeu, la seconde copie s'arrête toute seule, donc un appui sur la touche n'est traité qu'une fois.

**Lire une perk :** tant que la souris est libre (accroché, mort, spectateur), survole une icône de l'overlay pour voir son texte ; sors de l'icône et il disparaît. L'outil ne lit que la position de la souris (aucun crochet, rien n'est lu dans le jeu) : rien du tout quand l'overlay est caché, deux fois par seconde pendant que tu joues (le jeu cache et bloque le curseur), et une vérification rapide (25 fois par seconde) seulement quand la souris est libre **et** près des icônes. En jeu normal la souris est bloquée sur la caméra, donc rien ne s'affiche. `data/entity_toolkit.log` garde la trace : des lignes `Overlay hover:` à chaque changement (souris bloquée / libre, texte affiché / masqué) et un résumé du nombre de vérifications chaque minute.

Pourquoi l'overlay attend : la liste des survivants du jeu n'est visible qu'une fois le menu Tab refermé. Après l'appui, l'outil surveille l'écran, lit les noms de la liste du jeu et associe chaque allié à la bonne ligne, d'abord par **portrait**, puis par **pseudo** quand deux alliés jouent le même personnage ou que les portraits se ressemblent trop. Ta propre ligne ne bouge jamais.

## Mode automatique

Settings → Options commence par un choix : **Hotkey** (par défaut : tu appuies sur la touche de capture, modifiable juste en dessous) ou **Automatic**. En mode automatique, tu n'appuies plus sur la touche de capture :

1. **Au début du match, appuie sur Tab** comme tu le ferais de toute façon. L'outil voit le menu des joueurs, lit les perks et la map, et affiche l'overlay.
2. **Joue.** Rouvrir Tab ne relit pas le menu pendant 5 minutes.
3. **À la fin, reste deux secondes sur le tableau de fin.** Dès que chacun des quatre survivants a une icône d'état (échappé, mort, déconnecté), le tableau part sur NightLight et l'overlay est retiré. Si tu meurs en premier et que tu regardes le tableau pendant que les autres jouent encore, l'outil attend ; appuie sur la touche de capture si tu veux l'envoyer tout de suite.

La touche de capture et la touche qui retire l'overlay marchent exactement comme avant.

**Ce que ça coûte.** Tant que le jeu est la fenêtre au premier plan, l'outil regarde une fine bande en haut à gauche de l'écran (là où sont écrits *PLAYERS* et *MATCH SCOREBOARD*) toutes les 2 secondes, et trois fois dans les deux secondes qui suivent un appui sur Tab. Un coup d'œil prend environ 30 ms. Quand le jeu n'est pas au premier plan, il ne regarde rien.

**Ce que ça touche.** Rien de nouveau par rapport à la touche de capture : une capture de l'écran, l'état de la touche Tab, et la liste des programmes lancés pour savoir que le jeu est au premier plan. La mémoire et les fichiers du jeu ne sont jamais lus, et rien n'est envoyé au jeu. Comme toujours, aucune garantie vis-à-vis de l'anti-triche : voir le README.

**Limites.** Un tableau n'est envoyé que si les quatre lignes de survivants ont une icône d'état, donc un match personnalisé avec moins de survivants ne part pas tout seul : utilise la touche de capture. Après un tableau, le suivant ne part pas tout seul pendant 2 min 30 (pour que quitter la page puis y revenir ne l'envoie pas deux fois).
