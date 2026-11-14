# Contributing to Entity Toolkit

Thank you for wanting to help. This page says how to report a problem, propose a change and send code.

## Report a problem or an idea

Open an [issue](https://github.com/Tau-hub/entity-toolkit/issues/new/choose) and pick the matching form. For a bug, give the version (shown in Settings), what you did, what you expected and what happened, and the relevant lines of `data/entity_toolkit.log`. **Blur or remove player names, your NightLight token and any personal detail** before posting a log or a screenshot. Check the [Troubleshooting](https://github.com/Tau-hub/entity-toolkit/wiki/Troubleshooting) page first.

Security problems: see [SECURITY.md](SECURITY.md), not a public issue.

## Run it from the sources

```bash
git clone https://github.com/Tau-hub/entity-toolkit
cd entity-toolkit
install.bat        # Python 3.11+, installs requirements.txt
run.bat            # or: python -m entity_toolkit
python -m unittest discover -s tests
```

The tests use no game and no network. A change that touches what the toolkit reads on screen should also be checked on a real screenshot (`python -m entity_toolkit test-image file.jpg`, a dry run that sends nothing).

## Send a change

1. Fork, then create a branch from `main` (`fix/menu-bots`, `feat/tier-list`).
2. Keep the change small and about one thing. Add or update a test when behaviour changes.
3. Update the documentation that the change makes wrong: the [README](README.md) (EN and FR), the `wiki/` pages (EN and FR), the Settings page, and [CHANGELOG.md](CHANGELOG.md) (section *Unreleased*).
4. Anything the toolkit does by itself must be a setting in Settings, with a good default and a line in the docs.
5. Make sure the tests pass, then open a pull request with the template.

Screenshots published in the README or the wiki must be anonymised (no player names, no chat, no account details).

## Commit messages: Conventional Commits

```
type(scope): short summary in the imperative

Optional body: why the change was needed.
```

| Type | Use for |
|---|---|
| `feat` | a new feature |
| `fix` | a bug fixed |
| `docs` | README, wiki, comments, credits |
| `refactor` | code reorganised, same behaviour |
| `perf` | faster or lighter |
| `test` | tests only |
| `build`, `ci` | the `.exe` packaging, GitHub Actions |
| `chore` | everything else (`chore(release): 0.4.4`) |

A breaking change adds `!` (`feat(config)!: ...`) or a `BREAKING CHANGE:` line in the body. Scopes are free and short: `menu`, `overlay`, `automatic`, `window`, `tierlist`, `wiki`, `ci`...

If an AI tool wrote part of the change, say so in the pull request, and keep its `Co-Authored-By:` line in the commit.

## Releases (maintainer)

A release is made only when it is worth it for the people using the `.exe`, not for every change.

1. Update `CHANGELOG.md` (move *Unreleased* under the new version and date) and `__version__` in `entity_toolkit/__init__.py`; commit as `chore(release): X.Y.Z`.
2. Tag `vX.Y.Z` and push the tag: GitHub Actions runs the tests, builds the `.exe` zip with its `SHA256SUMS.txt` and a build attestation, and opens a **draft** release, which the maintainer publishes.
3. `python packaging/publish_wiki.py` publishes the wiki pages.

## Licences

The code is under the [MIT licence](LICENSE). The game data shipped in `seed/` is not: see [seed/README.md](seed/README.md), and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for the libraries. By sending a contribution you agree that it is published under the MIT licence.

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).
