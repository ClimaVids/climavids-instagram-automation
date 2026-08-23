# ClimaVids Instagram Automation

Automated Instagram comment processing and daily content preparation for ClimaVids using GitHub Actions and the Meta Instagram API.

## Current schedule

- `comment-bot.yml`: runs every 4 hours at minute 0 (`0 */4 * * *`, UTC).
- `daily-content.yml`: runs twice daily (`0 9 * * *` and `0 21 * * *`, UTC).
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Comment replies are enabled by the workflow when the required Meta secrets are configured.
- Daily publishing remains hard-disabled with `DRY_RUN = True`.
- Concurrency prevents overlapping comment/content runs.
- Runtime state lives only on the dedicated `state` branch in `state.json`.
- Rate-limit handling uses exponential backoff and respects `Retry-After` when available.
- Token expiry is inspected dynamically when the Meta app access token is available; less than 7 days remaining fails the workflow.

> **Cron note:** GitHub Actions cron schedules are UTC. The requested `09:00` and `21:00` values are therefore UTC unless the schedule is later changed to local-time equivalents.

## Free content services

### Pexels

`PEXELS_API_KEY` is used for optional photo/video discovery. Pexels is free and currently documents a default limit of 200 requests/hour and 20,000 requests/month; eligible applications can request higher limits for free. The code treats the service as optional and falls back safely when unavailable. Pexels attribution requirements must be respected when its media is used. citeturn477920search0turn477920search3

### Gemini

`GEMINI_API_KEY` is used for optional caption generation. Gemini free-tier limits vary by model and project and are measured using RPM/TPM/RPD rather than one universal request-per-day number, so no unverified fixed quota is hard-coded. The code falls back to a default Persian caption when Gemini is unavailable. citeturn477920search10turn477920search6

## Required GitHub Actions Secrets

Create these only under **Repository → Settings → Secrets and variables → Actions**. Never put values in source files, README values, issues, logs, or commits.

- `INSTAGRAM_ACCESS_TOKEN` — Meta/Instagram access token authorized for the selected Instagram Professional account.
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` — Instagram Professional account ID used by the API.
- `META_APP_ACCESS_TOKEN` — optional app access token used for dynamic token-expiry inspection via Meta's token-debugging flow.
- `PEXELS_API_KEY` — optional Pexels API key for media discovery.
- `GEMINI_API_KEY` — optional Gemini API key for caption generation.

Unused optional secrets do not need to be created.

## Safety boundaries

- `main` is not modified during this development phase.
- Comment replies are enabled only when Meta credentials are actually present in GitHub Actions Secrets.
- Daily content generation is allowed to prepare a draft caption/media reference, but **live Instagram publishing is disabled**.
- A missing or failing Pexels/Gemini service does not fail the daily content preparation step; safe fallbacks are used instead.
- Scheduled workflows do not receive production secrets from arbitrary fork pull requests.

## Runtime state format

The `state` branch contains:

```json
{
  "comment_ids": [],
  "last_run_at": null
}
```

State updates are isolated from application code history.

## Local tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_connection.py` is non-destructive and skips itself unless the Instagram credentials are present.

## Next steps

1. Configure and verify the Meta app, Instagram Professional account, token type and permissions.
2. Add the five Secrets listed above.
3. Run a controlled read-only test.
4. Confirm the first automated comment-reply cycle.
5. Keep daily publishing in Dry-Run until explicit approval.
