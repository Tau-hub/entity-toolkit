[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Data-and-privacy)

## Données et vie privée

Tout ce que l'outil enregistre vit dans le dossier `data/` (ignoré par git) à côté du code (modifiable avec la variable d'environnement `ENTITY_TOOLKIT_DATA`) :

| Fichier / dossier | Contenu |
|---|---|
| `icons/`, `images/`, `loadout_data.json`, `loadout_extra.json`, `patch.json`, `killers.json`, `survivors.json`, `survivor_builds.json`, `maps.json`, `nl_maps.json` | Téléchargés par **Update database** |
| `levels.json`, `levels_history.json`, `levels_backups.json`, `owned.json` | Tes niveaux, leur historique, les états gardés avant les changements en masse, et les personnages que tu ne possèdes pas |
| `my_builds.json`, `perk_types.json` | Tes builds de la Création de build, et tes corrections des types de perks |
| `captures/` | Les 100 dernières captures prises avec la touche (une rotation : la plus ancienne est supprimée ; le nombre se règle dans Settings, 0 = aucune) |
| `config.json` | Tes réglages (dont le délai de mise à jour automatique) |
| `nightlight_token.txt` | Ton jeton d'API NightLight. Envoyé **uniquement** à `api.nightlight.gg` |
| `nightlight_profile/` | Le profil Edge qui garde ta session NightLight |
| `uploads/`, `debug/` | Les tableaux envoyés et les dernières captures gardées pour diagnostiquer |
| `entity_toolkit.log` | Ce que l'outil a fait |

Réseau : la capture du jeu ne quitte jamais ton PC, sauf le **tableau de fin**, qui part vers NightLight quand tu appuies sur la touche dessus (désactive-le avec *Dry run* dans Settings). **Update database** lit `deadbydaylight.wiki.gg`, `otzdarva-builds.com`, `otzdarva.com`, `otz-addon-tierlist.pages.dev` et `nightlight.gg`. Une fois par jour, l'outil lit aussi un fichier public sur `raw.githubusercontent.com` pour te prévenir quand une nouvelle version existe (rien n'est envoyé ; désactivable dans Settings), et une fois par semaine la liste publique du Shrine of Secrets de NightLight sur `api.nightlight.gg` (rien n'est envoyé, pas de jeton ; désactivable dans Settings). Le serveur web local n'écoute que sur `127.0.0.1` et refuse les requêtes venant d'autres sites.
