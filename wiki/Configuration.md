[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Setup-and-settings)

## Premier lancement : la page Setup

![Page Setup, premier lancement](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/setup.png)

Au premier lancement, le Setup se fait **une page à la fois**, avec **Next** et **Back**. Rien n'est bloquant : tu peux passer une page et y revenir, et tout se retrouve ensuite dans **⚙ Settings**.

1. **Prérequis.** La page vérifie que Windows a un moteur OCR anglais.
2. **Update database.** Un bouton télécharge les noms, descriptions et icônes des perks (wiki DbD), les noms de maps, les builds et la tier list d'Otzdarva, et les stats de NightLight. La première fois, compte quelques minutes. Relance-le après un patch du jeu (nouveaux perks, nouvelles maps, nouvelles notes). La page indique le patch du jeu (d'après les annonces Steam) et l'étiquette de patch des données d'Otzdarva, qui peut avoir quelques jours de retard ; les pages du wiki sont retéléchargées à chaque mise à jour. Chaque étape rend compte séparément, donc un site en panne ne bloque pas les autres. Depuis une console : `python -m entity_toolkit update-db`. Pendant le téléchargement, la page indique l'étape en cours, puis ce que le patch a apporté (killers, survivants, perks, add-ons, objets, offrandes, maps ajoutés ou retirés). Une fois fait une première fois, l'outil rafraîchit les données tout seul tous les 7 jours en arrière-plan (modifiable ou désactivable dans *Options*). Clique sur le bouton puis sur **Next** : le téléchargement continue en arrière-plan pendant que tu remplis la suite (et **Next** le lance tout seul si tu l'as oublié).
3. **Hotkey or automatic.** Choisis comment l'outil se déclenche : en mode automatique (par défaut), où il suffit de garder le menu Tab ouvert environ une seconde au début du match, ou avec une touche de capture de ton choix (Alt + pavé numérique 7 tant que tu ne la changes pas ; la touche qui retire l'overlay se règle ici aussi) (voir [En match](https://github.com/Tau-hub/entity-toolkit/wiki/En-match#mode-automatique)).
4. **Your in-game name.** Saisis ton pseudo en jeu exactement comme sur le tableau de fin.
5. **NightLight** (facultatif). Le lien de la page mène à [nightlight.gg/account/api](https://nightlight.gg/account/api), où tu crées ton jeton d'API ; colle-le, puis connecte-toi une fois dans la fenêtre Edge qu'ouvre le bouton. L'outil ne voit jamais ton mot de passe. Tu n'utilises pas NightLight ? Clique sur **Next** : sans jeton, rien n'est jamais envoyé, même en mode automatique.
6. **Your character levels** (facultatif). Dépose des captures des écrans de sélection des tueurs et des survivants directement dans la page Setup : l'outil lit quels personnages tu as et leurs niveaux (tu vérifies avant d'enregistrer), ou règle-les à la main sur la page **Levels** (voir plus bas).
7. **Options.** Les réglages par défaut conviennent à la plupart des joueurs. Overlay oui/non, sons, icône dans la zone de notification, vérification d'une nouvelle version, fenêtre Entity Toolkit ou navigateur, ouverture sur la page Live au démarrage de l'outil (activée par défaut : avec le démarrage automatique, elle s'ouvre à chaque lancement du jeu), ce que fait la fermeture de la fenêtre, simulation (enregistre le tableau mais ne l'envoie jamais), l'encadré Shrine of Secrets, le démarrage avec Windows, et la fréquence de mise à jour automatique de la base.
8. **Done.** Un récapitulatif de ce qui est prêt et de ce qui a été passé, puis **Finish setup**, qui ouvre la page Live.

Chaque modification de la page est enregistrée dès que tu la fais (une petite note *Saved ✓* apparaît en bas à droite) : il n'y a pas de bouton d'enregistrement.

Quand tu appuies sur **Finish setup**, le bouton *Setup* devient **⚙ Settings** (en haut à droite) : le même contenu sur une seule page, sans les prérequis : mettre à jour la base, choisir touche ou automatique et tes touches, changer ton pseudo, régler le jeton NightLight, importer les niveaux, et les options. *Reset the setup* en bas refait apparaître le Setup page par page (tes données sont gardées).

![Page Settings](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/settings.png)

### La fenêtre Entity Toolkit

Les pages s'affichent dans une fenêtre à part, comme n'importe quel logiciel : pas de navigateur web, pas d'adresse à taper. Tu peux la déplacer, la redimensionner, la réduire et l'agrandir.

- **Où elle s'ouvre.** La première fois, au milieu de l'écran, à 75 % de sa taille, sur ton second écran si tu en as un (pour ne pas recouvrir le jeu). Ensuite, elle se rouvre là où tu l'as laissée, à la taille que tu lui as donnée.
- **La fermer.** La première fois, elle demande : **Keep it running** (la fenêtre disparaît, l'outil continue de lire tes parties depuis la zone de notification) ou **Quit Entity Toolkit** (tout s'arrête). Coche *Remember my choice* et elle ne demande plus ; le choix se retrouve dans les options (*When I close the window*).
- **La retrouver.** Double-clique sur le **E** rouge dans la zone de notification, ou relance le programme : la copie déjà lancée affiche sa fenêtre.
- **Avec le jeu.** Avec *Start automatically with Windows*, la fenêtre s'ouvre toute seule sur la page Live quand tu lances Dead by Daylight. L'outil s'arrête quand le jeu **et** la fenêtre sont tous les deux fermés.
- **Tu préfères ton navigateur ?** Décoche *Show the pages in the Entity Toolkit window* dans les options : les pages s'ouvrent alors dans ton navigateur par défaut, comme avant.

Sous le capot, rien n'a changé : la fenêtre affiche les mêmes pages locales, servies par l'outil sur ton PC uniquement, avec le moteur web intégré à Windows (WebView2, celui d'Edge). Si ce moteur est absent, l'outil se rabat tout seul sur ton navigateur.

### L'icône dans la zone de notification

Tant que l'outil tourne, un petit **E** rouge reste dans la zone de notification de Windows (en bas à droite de la barre des tâches, derrière la flèche **^** si Windows le masque). Il indique que l'outil est allumé, et c'est le moyen de retrouver la fenêtre une fois que tu l'as fermée :

- **Double-clic** : ouvre la page Live.
- **Clic droit** : un menu avec toutes les pages (Live, Levels, Killer priorities, Survivor priorities, Killer sheet, Survivor builds, Random loadout, Build creator), les deux défis du jour, **Settings**, puis **Quit Entity Toolkit**, qui arrête l'outil : la touche de capture ou le mode automatique, l'overlay et les pages locales.

Tu peux désactiver l'icône dans les options ; l'outil fonctionne pareil sans elle.
