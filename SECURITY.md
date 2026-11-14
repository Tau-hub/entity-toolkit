# Security policy

## Supported versions

Only the latest release receives fixes. Update from Settings (or download the latest release).

## Reporting a vulnerability

Please do **not** open a public issue. Open a private report: [Report a vulnerability](https://github.com/Tau-hub/entity-toolkit/security/advisories/new) (GitHub private vulnerability reporting). Say what you found, how to reproduce it and the version. You will get an answer as soon as the maintainer can; this is a small volunteer project, so give it a few days.

## What matters here

Entity Toolkit runs on your PC only. It listens on `127.0.0.1` (never on the network), reads the game's screen and the mouse position, never the game's memory or files, and keeps your NightLight token in `data/nightlight_token.txt`. Things worth reporting: a way for a web page or another program to reach the local server and act on it, a way to read the token, an update that does not check what it installs, a path traversal in the local server.

Release downloads come with a `SHA256SUMS.txt` and a GitHub build attestation; the self-update checks the SHA-256 before installing.
