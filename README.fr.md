# Entity Toolkit

Un compagnon **non officiel** pour *Dead by Daylight* (Windows) : voir les perks de tes alliés par-dessus le jeu, envoyer le tableau de fin de match à NightLight avec une seule touche, suivre le niveau de tes personnages, consulter des builds recommandés et créer les tiens.

[English version](README.md)

> Aucun lien avec Behaviour Interactive, NightLight, Otzdarva ni le wiki DbD. *Dead by Daylight* et ses éléments sont des marques et la propriété de Behaviour Interactive Inc. Les icônes de perks, les descriptions, les builds et les notes dont l'outil a besoin sont livrés avec lui dans le dossier [`seed/`](seed/README.md), qui indique la source et le propriétaire de chaque partie : ils ne sont pas couverts par la licence de ce projet, et sont ensuite tenus à jour sur ton PC.

![Les perks des alliés dessinés par-dessus la liste des survivants du jeu](docs/images/overlay.jpg)

*Les quatre perks de chaque allié, en grille 2×2 à côté de son portrait dans la liste des survivants du jeu (pseudos floutés pour cette capture).*

## Ce que ça fait

| | |
|---|---|
| **Perks des alliés** (survivant) | Dans le menu des joueurs (Tab), avec ta touche de capture ou tout seul en mode automatique, l'outil lit les perks, les noms de personnage et les pseudos de tes trois alliés, les affiche sur la page **Live** (second écran) et les dessine sur la liste des survivants du jeu, devant le bon survivant. |
| **Texte d'une perk au survol** | Quand le jeu libère la souris (tu es accroché ou mort), passe-la sur une icône de l'overlay : une petite boîte affiche le nom, la note et le texte de la perk. Elle disparaît dès que la souris quitte l'icône. À désactiver dans la page Settings. |
| **Mode automatique** (par défaut) | Aucune touche : Tab (menu ouvert environ une seconde) lit le menu des joueurs, et le tableau de fin part tout seul une fois le match terminé pour tout le monde. Tu préfères une touche ? Choisis *Hotkey* dans Settings. |
| **Mémoire de la map** (survivant et tueur) | La même touche lit et mémorise la map depuis le menu des joueurs. |
| **Envoi NightLight** | Sur le tableau de fin de match (même touche, ou tout seul en mode automatique), le match est envoyé à [NightLight](https://nightlight.gg) et la revue est faite pour toi (« Me » coché sur ton pseudo, les autres en Random, map réglée depuis la mémoire, Confirm cliqué). |
| **Suivi des niveaux** | Une page pour régler où tu en es avec chaque tueur et survivant, tenue à jour automatiquement depuis le tableau de fin. Les actions en masse demandent confirmation et peuvent être annulées. |
| **Priorités** | Quels personnages monter en priorité, d'après l'avis d'Otzdarva et les stats NightLight. La page affiche aussi les points de sang qui restent à dépenser pour amener tes killers, tes survivants, ou les deux, au niveau 3 (estimation d'environ 1 116 000 par niveau). |
| **Builds recommandés** | Fiches tueur (builds, tier list des add-ons, combos) et builds survivants, d'Otzdarva et de NightLight. |
| **Shrine of Secrets** | Les pages de priorités affichent les quatre perks du Shrine de la semaine et te disent lesquelles tu n'as pas encore et valent tes éclats. |
| **Loadout aléatoire** | Tire un loadout aléatoire de tueur (ou de survivant) : pouvoir, add-ons, perks, offrande en option, avec les notes. Filtres : seulement ce que tu as, une perk d'un type donné, une note minimale. L'affiche se copie ou se télécharge en image. |
| **Défi du jour** | Un loadout de tueur et un loadout de survivant par jour, les mêmes pour tout le monde : joue-le, coche-le, garde ta série. |
| **Création de build** | Enregistre tes propres builds killer et survivant (quatre perks, un nom, les killers concernés). Recherche de perks par nom, killer ou type : « aura », « gen regression », « healing »… |
| **Prêt dès l'installation** | Les perks, icônes, maps, builds et notes sont livrés avec l'outil. À chaque démarrage, il vérifie si le jeu a reçu un nouveau patch et les rafraîchit tout seul (seules les nouvelles icônes sont téléchargées) ; il le fait aussi tous les 7 jours. Tout est réglable. |
| **Se met à jour tout seul** | Quand une nouvelle version d'Entity Toolkit sort, il propose de l'installer : un clic, le téléchargement est vérifié (SHA-256), tes données sont gardées, l'outil redémarre. |
| **Sons** | Un son doux « ok » ou « pas ok » pour savoir sans regarder si la map et les perks ont été lus. |

![Page Live](docs/images/live.png)

*Les captures de ce README ont été prises sur un dossier de données de démonstration : niveaux et builds inventés, pseudos d'exemple.*

*(L'interface des pages est en anglais.)*

## Comment ça marche, et ce que ça ne fait pas

- L'outil **ne regarde que les pixels** : une capture de l'écran sur lequel est le jeu, comme OBS. Il **ne lit pas** la mémoire du jeu, n'injecte rien et ne s'accroche pas au jeu.
- Le texte est lu avec l'**OCR intégré à Windows** ; les icônes de perks sont reconnues en les comparant aux icônes officielles qu'il télécharge.
- L'overlay est une **fenêtre transparente séparée** posée par-dessus le jeu (les clics la traversent, elle ne prend jamais le focus), et non quelque chose dessiné dans le jeu.
- **Aucune garantie côté anti-triche.** Il se comporte comme les outils de capture d'écran et l'overlay de Discord, mais c'est à toi de décider si tu es à l'aise avec un programme lancé à côté d'un jeu en ligne. À tes risques.

## En match

L'outil agit à deux moments, le début et la fin d'une partie. Tu choisis dans Settings comment ils se déclenchent : **Automatic** (par défaut : aucune touche) ou **Hotkey** (une touche de capture de ton choix, Alt + pavé numérique 7 tant que tu ne la changes pas).

| | Mode automatique (par défaut) | Mode Hotkey |
|---|---|---|
| **Début de la partie** | Ouvre le menu des joueurs (Tab) et garde-le ouvert environ une seconde | Ouvre le menu des joueurs (Tab) et appuie sur ta touche de capture |
| **Fin de la partie** | Rien : il part quand les perks de tous les joueurs sont dévoilées | Appuie sur ta touche de capture sur le tableau de fin |

1. **Début : le menu des joueurs est lu.** Les perks de tes trois alliés et la map.
2. **Ferme le menu** : les quatre perks de chaque allié restent affichées à côté de son portrait, pendant tout le match. Ta touche qui retire l'overlay (Alt + pavé numérique 8 tant que tu ne la changes pas) les efface.
3. **Fin : le tableau de fin est lu** et, si tu as configuré NightLight, envoyé.
4. **Rien d'autre à faire** : le match est validé sur NightLight à ta place (ta ligne cochée, la map renseignée).

Le fonctionnement du mode automatique, ce qu'il coûte et ses limites : [Mode automatique](https://github.com/Tau-hub/entity-toolkit/wiki/En-match#mode-automatique).

Les mêmes étapes avec des captures : [En match](https://github.com/Tau-hub/entity-toolkit/wiki/En-match).

## Installation

Windows 10 ou 11, le jeu en **anglais** et en mode **fenêtré ou fenêtré sans bordure**. Deux façons, le même outil :

- **Le `.exe`, sans Python.** Télécharge le zip de la [dernière release](https://github.com/Tau-hub/entity-toolkit/releases/latest), dézippe-le, double-clique sur `EntityToolkit.exe`.
- **Avec Python 3.10+.** `git clone https://github.com/Tau-hub/entity-toolkit`, puis `install.bat` et `run.bat`.

Entity Toolkit ouvre **sa propre fenêtre** (pas de navigateur, pas d'adresse à taper) sur la page **Setup**, qui te guide pour le reste. Les détails, comment vérifier l'empreinte SHA-256 du téléchargement et quoi faire de l'avertissement Windows SmartScreen : [Installer](https://github.com/Tau-hub/entity-toolkit/wiki/Installer).

## Documentation

Le mode d'emploi est sur le [wiki](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) :

| Page | Ce que tu y trouves |
|---|---|
| [Installer](https://github.com/Tau-hub/entity-toolkit/wiki/Installer) | Prérequis, le `.exe` ou Python, vérifier le téléchargement, avertissements de Windows |
| [Configuration](https://github.com/Tau-hub/entity-toolkit/wiki/Configuration) | Le Setup du premier lancement page par page, mode touche ou automatique, toutes les options, l'icône de la zone de notification |
| [En match](https://github.com/Tau-hub/entity-toolkit/wiki/En-match) | Pas à pas avec captures, en mode touche et en mode automatique : perks des alliés, overlay, envoi NightLight |
| [Niveaux et priorités](https://github.com/Tau-hub/entity-toolkit/wiki/Niveaux-et-priorites) | Suivre tes niveaux, qui monter en priorité, l'alerte Shrine of Secrets |
| [Builds et loadouts](https://github.com/Tau-hub/entity-toolkit/wiki/Builds-et-loadouts) | Builds recommandés, loadout aléatoire et ses filtres, défi du jour, création de build |
| [Données et vie privée](https://github.com/Tau-hub/entity-toolkit/wiki/Donnees-et-vie-privee) | Ce qui est stocké, où, et ce qui passe par le réseau |
| [Dépannage](https://github.com/Tau-hub/entity-toolkit/wiki/Depannage) | Rien ne se passe, un allié ou une perk manquant, tableau non envoyé, overlay décalé, revue NightLight |
| [Ligne de commande et développement](https://github.com/Tau-hub/entity-toolkit/wiki/Ligne-de-commande-et-developpement) | Commandes, tests, modules, comment une version est publiée |

## Crédits

Les builds, les valeurs de perks et la tier list des add-ons viennent d'**Otzdarva** ([otzdarva-builds.com](https://otzdarva-builds.com), [otzdarva.com](https://otzdarva.com)) ; les statistiques de la communauté et l'API d'envoi de **[NightLight](https://nightlight.gg)** ; les données de perks et de maps du **[wiki Dead by Daylight](https://deadbydaylight.wiki.gg)**. Une copie de ces données est livrée avec l'outil pour qu'il marche dès l'installation ([`seed/`](seed/README.md) dit ce qui vient d'où) ; elles restent la propriété de leurs auteurs, et sont retirées sur demande.

## Licence

[MIT](LICENSE) pour le code de ce dépôt. Elle ne couvre ni les données tierces que l'outil livre dans [`seed/`](seed/README.md) ou télécharge, ni les éléments de *Dead by Daylight*.

## Assistance de l'IA

L'essentiel du code et de la documentation de ce projet a été écrit avec Claude (Anthropic) via Claude Code, à partir des besoins du mainteneur. Le mainteneur a choisi les fonctionnalités, relu les résultats et vérifié l'outil sur de vraies captures de jeu et en match. Comme pour tout code assisté par IA, il reste probablement des bugs et des configurations non gérées : lis ce que fait l'outil avant de lui donner accès à ton compte NightLight. Les commits contenant des changements écrits par l'IA portent une ligne `Co-Authored-By: Claude`. Les contributions sont bienvenues ; si un outil d'IA en a écrit une partie, dis-le dans la pull request.
