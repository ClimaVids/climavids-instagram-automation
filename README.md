# ClimaVids Instagram Automation

Automated Instagram comment processing and daily content preparation for ClimaVids using GitHub Actions and the Meta Instagram API.

## Current schedule

- `comment-bot.yml`: runs every 4 hours at minute 0 (`0 */4 * * *`, UTC).
- `daily-content.yml`: uses one scheduler entry (`*/15 6-8,16-18 * * *`, UTC) and the application performs the exact Iran-local time check.
- Iran Feed windows: **10:00–12:00** and **20:00–22:00** Asia/Tehran time.
- The Feed strategy is now **one post per Iran-local day**, not two. The 70% chance gate only selects an irregular run inside an eligible window; runtime state prevents a second Feed post that day.
- The windows are centered around useful activity periods near **11:00** and **21:00**, while the exact successful run is intentionally variable.
- An optional **daily Story** feature is now implemented as a separate publishing boundary. It prepares one Story per day and remains Dry-Run until explicit approval.
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Comment replies are enabled by the workflow when the required Meta secrets are configured.
- Daily Feed and Story publishing remain hard-disabled with `DRY_RUN = True` until explicit approval.
- Concurrency prevents overlapping application runs.
- Runtime state lives only on the dedicated `state` branch in `state.json`.
- Rate-limit handling uses exponential backoff and respects `Retry-After` when available.
- Token expiry is inspected dynamically when the Meta app access token is available; less than 7 days remaining fails the workflow.

> **Cron note:** GitHub Actions cron schedules are UTC. The application converts the current time to `Asia/Tehran` before applying the publishing windows.

## Natural-language and quality-first content

Because Feed frequency has been reduced to once per day, Gemini is instructed to produce deeper, more accurate and more useful captions: explain the mechanism behind the phenomenon, its practical significance, and one concrete takeaway, while avoiding unsupported facts and robotic phrasing.

The requested Persian style is warm, conversational, friendly and natural, similar to an experienced meteorologist or climate enthusiast speaking directly to the audience.

The application includes **20 varied Persian fallback captions** and **20 varied comment replies**, so Gemini is optional rather than a hard dependency. When Gemini is unavailable or rate-limited, predefined text is used automatically.

Comment replies can optionally be personalized by Gemini with `ENABLE_AI_REPLIES=true`; failures fall back immediately to the predefined replies.

## Optional daily Story

`src/story_publisher.py` prepares a daily Story concept, using an optional Pexels portrait asset and a short Gemini-generated Persian text. Meta's current Instagram API documentation supports `STORIES` media containers for Instagram Professional publishing, with Stories available to Business accounts in the Facebook Login setup. The project therefore keeps Story publishing modular and disabled until the account type, permissions and media requirements are verified. citeturn237608search0turn237608search2

## Free content services

### Pexels

`PEXELS_API_KEY` is used for optional photo/video discovery. Pexels documents a default limit of 200 requests/hour and 20,000 requests/month. Errors, missing keys, empty results and rate limits fall back to cached or empty media metadata without stopping the content cycle.

### Gemini

`GEMINI_API_KEY` is used for optional caption and reply generation. Gemini free-tier limits vary by model and project and are measured using RPM/TPM/RPD rather than one universal request-per-day number, so no fixed quota is hard-coded. Errors and quota exhaustion fall back to predefined Persian text.

## Required GitHub Actions Secrets

Create these only under **Repository → Settings → Secrets and variables → Actions**. Never put values in source files, issues, logs or commits.

- `INSTAGRAM_ACCESS_TOKEN` — Meta/Instagram access token authorized for the selected Instagram Professional account.
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` — Instagram Professional account ID used by the API.
- `META_APP_ACCESS_TOKEN` — optional app access token used for dynamic token-expiry inspection.
- `PEXELS_API_KEY` — optional Pexels API key for media discovery.
- `GEMINI_API_KEY` — optional Gemini API key for caption/reply generation.

Optional services do not need to be configured for the core scheduler to remain operational.

## Safety boundaries

- `main` is not modified during this development phase.
- Comment replies may be sent only when Meta credentials are configured and the comment workflow is taken out of dry-run mode.
- Daily Feed and Story preparation may fetch media and generate text, but **live Instagram publishing is disabled**.
- A missing or failing Pexels/Gemini service does not fail the daily content cycle; safe fallbacks are used instead.
- Scheduled workflows do not receive production secrets from arbitrary fork pull requests.

## Runtime state format

The `state` branch contains runtime information such as processed comment IDs, the last execution timestamp, the last Feed post date and the last Story date.

```json
{
  "comment_ids": [],
  "last_run_at": null,
  "metadata": {
    "last_feed_post_date": null,
    "last_story_date": null
  }
}
```

## Local tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_connection.py` is non-destructive and skips itself unless the Instagram credentials are present.
