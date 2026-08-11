# Changelog

## v8 - 2026-08-11
- Regenerated `SCHEMA.md` to include `tire_stints.csv`, `weather.csv`, and `practice_results.csv` (it had gone stale after those tables were added).

## v7 - 2026-08-11
- Added `practice_results.csv`: FP1/FP2/FP3 session results (best lap time, laps, rank) per driver per race, sourced from official F1 live timing via FastF1. Covers the 2025/2026 races only. Reserve/test drivers who only ran practice are excluded.

## v6 - 2026-08-11
- Added `weather.csv`: per-race weather summary (air/track temp, humidity, wind, rainfall flag), sourced from official F1 live timing via FastF1. Covers the 2025/2026 races only.

## v5 - 2026-08-11
- Added `tire_stints.csv`: tire compound and stint length per driver per race, sourced from official F1 live timing via FastF1. Covers the 2025/2026 races only.

## v4 - 2026-08-11
- Added `SCHEMA.md` (standalone column reference) and this changelog.

## v3 - 2026-08-10
- Backfilled `lap_times.csv` for all 35 completed 2025/2026 races (+39,357 rows). Previously skipped due to Jolpica API rate limiting; fetched race-by-race on a slower schedule this time.

## v2 - 2026-08-09
- Added per-file and per-column descriptions across all 14 tables.
- Fixed `results.csv`/`sprint_results.csv` `position` column to correctly use `\N` for unclassified (DNF/DSQ/etc) drivers, matching the base dataset's convention. This also corrected `positionOrder` sorting for those rows.

## v1 - 2026-08-09
- Initial release: extended the base Formula 1 World Championship (1950-2020) dataset with the full 2025 season (24 races) and every completed 2026 round through the Hungarian Grand Prix (round 11).
- New entities added: 18 drivers, 2 constructors (Audi, Cadillac), 1 circuit (Madring), 2 status codes (Lapped, Did not start).
- `lap_times.csv` intentionally left unchanged for 2025/2026 (see v3).
