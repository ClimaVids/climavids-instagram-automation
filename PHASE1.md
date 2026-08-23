# Phase 1 scaffold

Implemented on the `develop` branch:

- Four-hour comment workflow in dry-run mode.
- Daily content workflow in dry-run mode.
- CI tests.
- Minimal GitHub Actions permissions.
- Concurrency controls.
- Instagram API client with retry/backoff for transient responses.
- State model intended for the dedicated `state` branch.
- Comment duplicate/owner-reply guard.
- Token-expiry threshold configuration documented as 7 days.
- No live Meta credentials or secrets in source.

The live Meta integration is deliberately deferred until account permissions and token type are verified.
