# Security Policy

## Scope

This repository contains automation for Instagram/Meta APIs and related content preparation. Security issues involving access tokens, GitHub Actions, dependency supply chain, unintended publishing, or unauthorized state changes should be reported promptly.

## Never commit secrets

Do not commit Meta access tokens, app secrets, Telegram bot tokens, cookies, passwords, or private keys.

If a credential is suspected to be exposed, revoke or rotate it rather than relying on deleting the value from a later commit.

## Pull requests

Forked pull requests must not receive production secrets. Workflows should use read-only permissions unless a job explicitly requires otherwise. Security changes should be made on a branch and validated by CI before merge.

## Live mode

Live Instagram replies and publishing stay disabled until API permissions, account ownership, token handling, and dry-run behavior are verified.

## Reporting

Please do not publish credentials, access tokens, or exploitable details in a public issue. Report suspected vulnerabilities privately to the repository owner through the available private GitHub security-reporting mechanism.

Include the affected workflow or source file, concise reproduction steps, observed impact, whether a secret may have been exposed, and the relevant commit or workflow-run identifier.

## Security principles

- Live Instagram writes remain disabled by `DRY_RUN` unless explicitly approved.
- Meta Graph hosts are restricted to official HTTPS endpoints.
- GitHub Actions use least-privilege permissions and immutable action references where practical.
- Runtime state is kept on the dedicated `state` branch rather than modifying application source on `main`.
