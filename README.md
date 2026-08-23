# ClimaVids Instagram Automation

Automated Instagram comment processing and daily content preparation for ClimaVids using GitHub Actions and the Meta Instagram API.

## Current schedule

- `comment-bot.yml`: runs every 4 hours at minute 0 (`0 */4 * * *`, UTC).
- `daily-content.yml`: polls every 15 minutes (`*/15 * * * *`, UTC); the application decides whether to prepare a post.
- Iran publishing windows: **10:00–12:00** and **20:00–22:00** Asia/Tehran time.
- Each eligible scheduler run uses `RANDOM_POST_CHANCE=70`; therefore a run may be skipped even inside a window, producing irregular timing.
- The two-hour windows are centered around the commonly useful **11:00** and **21:00** activity periods, but the actual run is intentionally variable rather than fixed.
- A content slot is recorded in runtime state so that once live publishing is enabled, no more than one post is allowed per window per day.
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Comment replies are enabled by the workflow when the required Meta secrets are configured.
- Daily publishing remains hard-disabled with `DRY_RUN = True` until explicit approval.
- Concurrency prevents overlapping application runs.
- Runtime state lives only on the dedicated `state` branch in `state.json`.
- Rate-limit handling uses exponential backoff and respects `Retry-After` when available.
- Token expiry is inspected dynamically when the Meta app access token is available; less than 7 days remaining fails the workflow.

> **Cron note:** GitHub Actions cron schedules are UTC. The application converts the current time to `Asia/Tehran` before applying the 10:00–12:00 and 20:00–22:00 windows.

## Natural-language content

Gemini is prompted to write short Persian Instagram captions in a warm, conversational, friendly voice similar to an experienced meteorologist or climate enthusiast. It may include an audience question when useful.

The application includes **20 varied Persian fallback captions** so Gemini is optional rather than a hard dependency. When Gemini is unavailable or rate-limited, the fallback list is used and rotated randomly.

Comment replies also have **20 varied fallback messages**. Gemini-based comment personalization is optional (`ENABLE_AI_REPLIES=true` by default); when it fails, the predefined replies are used automatically.

## Free content services

### Pexels

`PEXELS_API_KEY` is used for optional photo/video discovery. Pexels documents a default limit of 200 requests/hour and 20,000 requests/month. The service is treated as optional: errors, missing keys, empty results, and rate limits fall back to cached or empty media metadata without stopping the content cycle.

### Gemini

`GEMINI_API_KEY` is used for optional caption and reply generation. Gemini free-tier limits vary by model and project and are measured using RPM/TPM/RPD rather than one universal request-per-day number, so no fixed quota is hard-coded. Errors and quota exhaustion fall back to predefined Persian text.

## Required GitHub Actions Secrets

Create these only under **Repository → Settings → Secrets and variables → Actions**. Never put values in source files, README values, issues, logs, or commits.

- `INSTAGRAM_ACCESS_TOKEN` — Meta/Instagram access token authorized for the selected Instagram Professional account.
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` — Instagram Professional account ID used by the API.
- `META_APP_ACCESS_TOKEN` — optional app access token used for dynamic token-expiry inspection.
- `PEXELS_API_KEY` — optional Pexels API key for media discovery.
- `GEMINI_API_KEY` — optional Gemini API key for caption/reply generation.

Optional services do not need to be configured for the core scheduler to remain operational.

## Safety boundaries

- `main` is not modified during this development phase.
- Comment replies may be sent only when Meta credentials are configured and the comment workflow is taken out of dry-run mode.
- Daily content preparation can fetch media and generate text, but **live Instagram publishing is disabled**.
- A missing or failing Pexels/Gemini service does not fail the daily content cycle; safe fallbacks are used instead.
- Scheduled workflows do not receive production secrets from arbitrary fork pull requests.

## Runtime state format

The `state` branch contains runtime information such as processed comment IDs, the last execution timestamp, and the last live content slot when publishing is eventually enabled.

```json
{
  "comment_ids": [],
  "last_run_at": null,
  "metadata": {
    "last_content_slot": null
  }
}
```

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

Phase update: irregular scheduling, natural-language fallbacks, and optional AI reply personalization are now part of the develop implementation.
