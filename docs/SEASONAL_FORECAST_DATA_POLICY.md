# Seasonal Forecast Data Policy

## Purpose

ClimaVids content may use a seasonal forecast only when the underlying values are traceable to an official, machine-readable forecast dataset or a dedicated parser for an official report.

## Official sources

- ECMWF SEAS5: official 2 m temperature and precipitation seasonal products and Open Charts.
- NOAA/NCEP CFSv2: operational global seasonal forecasts, including GRIB2 products exposed through NCEP NOMADS.
- IRIMO: official Iranian Meteorological Organization material; report-specific parsing is required before numeric values are accepted.

## Non-fabrication rule

HTML catalog text, chart-page prose, labels, publication metadata, or unrelated numbers must never be interpreted as forecast values. Until a dedicated numeric adapter produces validated values, the source record must keep `numeric` empty and the publisher must refuse to create a quantitative post.

## Current phase

The fetcher verifies that official sources are reachable and records provenance. CFS availability is also probed on the NCEP NOMADS production directory. Numeric extraction remains intentionally disabled pending a dedicated GRIB2/report adapter.
