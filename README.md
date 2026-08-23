# ClimaVids Instagram Automation

Automated Instagram comment processing and daily content publishing for ClimaVids using GitHub Actions and the Meta Instagram API.

## Phase 1 status

- `comment-bot.yml`: scheduled every 4 hours.
- `daily-content.yml`: scheduled once daily.
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Both workflows are **dry-run only** until Meta credentials and live permissions are verified.
- `concurrency` prevents overlapping runs of the same job.
- Runtime state is designed for the dedicated `state` branch.
- Retry/backoff is implemented for transient Meta API responses.
- Token-expiry monitoring will use the expiry actually reported by the platform rather than a hard-coded token lifetime.

## Required GitHub Actions Secrets (live phase)

Do **not** put these values in source code, README files, issues, logs, or commits.

Planned secrets/configuration:

- `INSTAGRAM_ACCESS_TOKEN` — Meta/Instagram access token used by the bot.
- `INSTAGRAM_ACCOUNT_ID` — Instagram professional account ID used by the API calls.
- `META_APP_ID` — Meta application ID when required by the selected authentication flow.
- `META_APP_SECRET` — Meta application secret; store only as a GitHub Actions secret.
- `ALERT_TELEGRAM_BOT_TOKEN` — optional, only if Telegram alerts are enabled.
- `ALERT_TELEGRAM_CHAT_ID` — optional, only if Telegram alerts are enabled.

The exact minimum set will be reduced after the Meta app/account configuration is verified. Unused secrets should not be created.

## State branch

The `state` branch is reserved for runtime JSON state such as processed comment IDs and token metadata. Main application branches should not contain live runtime state.

State writes must be atomic and should verify the branch tip before updating to avoid lost updates.

## Security

- No secrets in Git-tracked files.
- Workflow `permissions` are explicitly minimized.
- Fork pull requests must never receive production Instagram/Meta secrets.
- Live publishing remains disabled until dry-run checks and API permission tests pass.
- Do not enable write permissions for workflows unless a specific operation requires them.

## Local tests

```bash
python -m unittest discover -s tests -v
```

## Next phase

1. Verify the Meta app, Instagram professional account, permissions and token type.
2. Implement real comment retrieval and owner-reply detection.
3. Implement state synchronization with the `state` branch.
4. Add dynamic token-expiry inspection and alerting when the remaining lifetime is below the configured threshold.
5. Keep live replies disabled until a controlled test succeeds.
6. Implement daily media generation and publishing after comment automation is stable.
