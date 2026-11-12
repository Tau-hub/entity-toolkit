[← Accueil](https://github.com/Tau-hub/entity-toolkit/wiki/Accueil) · [English](https://github.com/Tau-hub/entity-toolkit/wiki/Installation)

## Prérequis

- Windows 10 ou 11 et Microsoft Edge (utilisé pour la revue NightLight ; son moteur web, WebView2, affiche aussi la fenêtre Entity Toolkit et fait partie de Windows 11 et de Windows 10 à jour). **Python 3.10 ou plus récent** seulement si tu choisis l'installation Python ci-dessous ; le `.exe` n'a besoin de rien d'autre.
- *Dead by Daylight* en **anglais**, en mode **sans bordure ou fenêtré** (pas en plein écran exclusif).
- Un **pack de langue anglais** pour l'OCR de Windows : Paramètres → Heure et langue → Langue et région.
- Testé en **2560×1440** pour le jeu et en **1920×1080** pour les écrans annexes. Toutes les positions sont proportionnelles à la hauteur de l'écran du jeu, mais les autres résolutions n'ont pas été testées : voir [Dépannage](https://github.com/Tau-hub/entity-toolkit/wiki/Depannage).

## Installation

Il y a deux façons de lancer l'outil. Elles font exactement la même chose : prends celle avec laquelle tu es à l'aise.

### Option A : le `.exe` (sans Python)

1. Ouvre la [dernière release](https://github.com/Tau-hub/entity-toolkit/releases/latest) et télécharge `EntityToolkit-<version>-windows.zip`.
2. Vérifie le téléchargement (facultatif mais conseillé, voir plus bas).
3. Dézippe-le où tu veux, dans un dossier où tu peux écrire (Documents, Bureau, un autre disque : pas `Program Files`). Garde `EntityToolkit.exe` et le dossier `_internal` ensemble.
4. Double-clique sur **`EntityToolkit.exe`**. Il démarre en arrière-plan (le **E** rouge apparaît dans la zone de notification) et ouvre sa fenêtre sur la page **Setup** la première fois.

Tes données vont dans un dossier `data` à côté de `EntityToolkit.exe`. L'outil propose lui-même la mise à jour quand une nouvelle release sort (voir [Configuration](https://github.com/Tau-hub/entity-toolkit/wiki/Configuration)) ; à la main, dézippe la nouvelle release par-dessus l'ancienne en gardant ton dossier `data`.

**Vérifier le téléchargement.** Chaque release est accompagnée de `SHA256SUMS.txt`, et ses notes affichent la même empreinte. Dans PowerShell, dans le dossier où se trouve le zip :

```powershell
Get-FileHash .\EntityToolkit-<version>-windows.zip -Algorithm SHA256
```

La valeur doit être celle de `SHA256SUMS.txt`. Sinon, le fichier n'est pas celui qui a été publié : supprime-le. Le zip est construit par GitHub Actions à partir du code source du tag ([release.yml](https://github.com/Tau-hub/entity-toolkit/blob/main/.github/workflows/release.yml)), pas sur le PC de quelqu'un, et GitHub signe une attestation qui le dit. Avec le [GitHub CLI](https://cli.github.com), tu peux vérifier cette attestation, qui prouve que le fichier sort bien du workflow de ce dépôt :

```bash
gh attestation verify EntityToolkit-<version>-windows.zip --repo Tau-hub/entity-toolkit
```

**Avertissements de Windows.** Le `.exe` n'est pas signé avec un certificat payant, donc Windows SmartScreen peut afficher *« Windows a protégé votre ordinateur »* la première fois : **Informations complémentaires → Exécuter quand même**. Les programmes empaquetés de cette façon (PyInstaller) sont aussi parfois signalés à tort par les antivirus. Si tu préfères ne pas faire confiance à un binaire, prends l'option B : elle exécute exactement le même code, que tu peux lire.

### Option B : avec Python

```bash
git clone https://github.com/Tau-hub/entity-toolkit
cd entity-toolkit
install.bat
run.bat
```

`install.bat` installe les paquets Python. `run.bat` lance l'outil en arrière-plan et ouvre sa fenêtre sur la page **Setup** la première fois. L'outil propose de se mettre à jour quand une nouvelle release sort (il lance `git pull` pour toi).
