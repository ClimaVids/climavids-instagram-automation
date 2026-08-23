# Security policy

## Never commit secrets

Do not commit Meta access tokens, app secrets, Telegram bot tokens, cookies, passwords, or private keys.

## Pull requests

Forked pull requests must not receive production secrets. Workflows should use read-only permissions unless a job explicitly requires otherwise.

## Live mode

Live Instagram replies and publishing stay disabled until API permissions, account ownership, token handling, and dry-run behavior are verified.
