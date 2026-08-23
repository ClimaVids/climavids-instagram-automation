# ClimaVids Instagram Automation

Automated Instagram comment processing and daily content publishing for ClimaVids using GitHub Actions and the Meta Instagram API.

## Phase 1

- `comment-bot.yml`: runs every 4 hours at minute 0 (`0 */4 * * *`, UTC).
- `daily-content.yml`: runs once daily at 00:00 UTC (`0 0 * * *`).
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Daily publishing is hard-disabled with `DRY_RUN = True`.
- Comment replies are also dry-run until live approval and verified Meta permissions.
- Concurrency is shared so comment and content jobs do not overlap.
- Runtime state lives only on the dedicated `state` branch in `state.json`.
- State updates use a temporary Git worktree and atomic commit/push.
- Rate-limit handling uses exponential backoff: 1, 2, 4, 8, 16 seconds, with `Retry-After` respected where available.
- Token expiry is inspected dynamically when `META_APP_ACCESS_TOKEN` is available; the workflow fails if less than 7 days remain.

> **Cron correction:** `*/4 * * * *` means every 4 minutes in standard cron syntax. Because this project requires every 4 hours, the correct GitHub Actions expression is `0 */4 * * *`.

## Required GitHub Actions Secrets for the live phase

Create these only under **Repository → Settings → Secrets and variables → Actions**. Never put values in source files, README, issues, logs, or commits.

- `INSTAGRAM_ACCESS_TOKEN` — access token authorized for the selected Instagram Professional account and required permissions.
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` — the Instagram Professional account ID used by the API.

### Optional token-expiry inspection secret

- `META_APP_ACCESS_TOKEN` — app access token required by Meta's `debug_token` endpoint to inspect `expires_at` / `data_access_expiration_time`. Without it, the bot logs that token expiry cannot be inspected rather than inventing a lifetime.

## Current Meta API behavior used by this project

Meta's current Instagram API documentation shows comment retrieval through the media `/comments` edge and private replies through the professional account `/messages` endpoint with `recipient.comment_id`. A private reply is limited to one message per commenter and must be sent within 7 days of the comment for posts/reels. Live has separate limitations.

The project intentionally keeps the API version configurable through `META_API_VERSION` and does not hard-code undocumented rate limits.

## Runtime state format

The `state` branch contains:

```json
{
  "comment_ids": [],
  "last_run_at": null
}
```

Only successfully considered comments are added to the state. A future storage backend can replace this interface without changing the comment-processing logic.

## Security model

- `main` is not modified during Phase 1 development.
- Secrets are never committed.
- Workflow permissions are explicit and minimal: the comment job needs `contents: write` solely to update the `state` branch; the daily job is read-only.
- Scheduled workflows do not execute code from arbitrary fork pull requests.
- Live Instagram writes remain disabled until a controlled test and explicit approval.

## Local tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_connection.py` is non-destructive and skips itself unless the required Instagram credentials are present.

## Planned next steps

1. Verify the Meta app, Instagram Professional account, token type, and permissions.
2. Test read-only account and comment retrieval.
3. Run the scheduler in dry-run mode and inspect logs/state behavior.
4. Perform one controlled private-reply test.
5. Only after approval, enable live comment replies.
6. Build the daily media-generation and publishing pipeline separately.
