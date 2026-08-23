# ClimaVids Instagram Automation

Automated Instagram comment processing and seasonal-forecast content preparation for ClimaVids using GitHub Actions and the Meta Instagram API.

## Scientific identity and scope

This project is now dedicated exclusively to **seasonal forecasting for Iran**. It is scientifically branded as:

- **Dr. Hossein Imanipour (دکتر حسین ایمانی‌پور)** — PhD in Climatology / Atmospheric Sciences.
- **ClimaVids** — the public-facing climate and weather brand.

Feed and Story content must be derived from current or cached seasonal-forecast evidence. The system must never replace missing forecast evidence with generic weather content or invented values.

Generated captions identify the analysis as Dr. Imanipour's interpretation of global-model guidance, while clearly distinguishing model guidance from certainty.

## Forecast-data sources

### ECMWF / SEAS5

Official ECMWF seasonal products are published as SEAS5 seasonal forecasts, including monthly means, anomalies, ensemble information and teleconnection-related products. ECMWF also provides public seasonal Open Charts.

Important licensing/access note: ECMWF's public Open Data page states that only a subset of real-time forecast data is free and open. The full SEAS5 raw catalogue is a separate product family. Therefore this project does **not** assume that unrestricted raw SEAS5 files are free. The adapter uses official public ECMWF seasonal chart/catalogue evidence and never fabricates raw SEAS5 numbers.

### NOAA/NCEP CFSv2

NOAA/NCEI documents CFSv2 operational forecasts with **9-month forecasts available to the present**, four cycles per day, with monthly means and other public HTTPS/TDS access paths. This is the primary freely accessible numerical seasonal source in the initial implementation.

### IRIMO

The system performs a best-effort scan of the official Iran Meteorological Organization website for current seasonal outlook/report links. Because official pages may change structure or availability, the result is cached and treated as supporting evidence rather than a source of invented numbers.

## Seasonal forecast pipeline

`src/seasonal_forecast_fetcher.py` fetches the three source families, stores the latest validated result in a persistent cache, and falls back to the last valid cache on temporary outages.

The output is explicitly marked as one of:

- `numeric_or_mixed` — at least one source provided numeric evidence.
- `official-source-metadata-only` — authoritative seasonal source evidence exists but no safe numeric value was parsed.
- `none` — no current or cached evidence is available.

The content generator is allowed to create a post only when current or cached forecast evidence exists. When no evidence is available, the run stops without producing generic content.

## Content identity and structure

Each post should cover, where supported by the data:

1. A scientific, attention-grabbing seasonal title.
2. Seasonal precipitation and temperature outlook for Iran.
3. Exact numeric values only when available, with units and source attribution.
4. Anomaly relative to the relevant reference climate when the source provides it.
5. Regional contrasts within Iran when supported by the source.
6. Large-scale drivers such as ENSO/NAO only when the source evidence supports the statement.
7. Responsible implications for water resources, agriculture and risk management.
8. A natural audience question to encourage discussion.

Gemini is explicitly instructed to explain uncertainty and never invent numbers or mechanisms.

## Current schedule

- `comment-bot.yml`: runs every 4 hours at minute 0 (`0 */4 * * *`, UTC).
- `daily-content.yml`: uses one scheduler entry (`*/15 6-8,16-18 * * *`, UTC) and the application performs the exact Iran-local time check.
- Iran Feed windows: **10:00–12:00** and **20:00–22:00** Asia/Tehran time.
- The Feed strategy is **one post per Iran-local day**. The 70% chance gate only selects an irregular run inside an eligible window.
- An optional daily Story preparation step is present; live Story publishing is disabled.
- Standard `ubuntu-latest` GitHub-hosted runners only.
- Daily Feed and Story publishing remain `DRY_RUN=True` until explicit approval.

## Free content services

### Gemini

`GEMINI_API_KEY` is optional. Free-tier limits vary by model and project, so no fixed quota is hard-coded. Forecast posts stop safely rather than turning into generic content when Gemini is unavailable.

### Pexels

`PEXELS_API_KEY` is optional and used only for visual asset discovery. Missing keys, temporary failures and rate limits fall back to cached media metadata or no media; they never create unsupported forecast claims.

## Required GitHub Actions Secrets

- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- `META_APP_ACCESS_TOKEN` (optional, for dynamic token-expiry inspection)
- `PEXELS_API_KEY` (optional)
- `GEMINI_API_KEY` (optional)

Never put values in source code, README files, issues, logs or commits.

## Runtime state

The `state` branch stores processed comment IDs, execution timestamps, forecast cache data and publishing markers. Runtime forecast cache includes the latest source responses so a temporary outage does not force the system into generic content.

## Safety boundaries

- `main` is not modified during development.
- No forecast numbers are invented.
- No generic weather post is produced when seasonal evidence is unavailable.
- Live Feed and Story publishing remain disabled until explicit approval.
- Temporary source outages use the last valid cache when available.

## Local tests

```bash
python -m unittest discover -s tests -v
```
