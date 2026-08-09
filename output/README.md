# Formula 1 World Championship (1950-2026)

**Maintained by:** Atharv Ranjan

## What was added

- **35 new completed races**: the full 2025 season (24 races) plus every completed round of the 2026 season through the **Hungarian Grand Prix (2026-07-26, round 11)**.
- New rows appended to: `races`, `results`, `qualifying`, `sprint_results`, `pit_stops`, `driver_standings`, `constructor_standings`, `constructor_results`, `drivers`, `constructors`, `circuits`, `status`, and `seasons`.
- **New entities introduced** (reused existing IDs wherever a driver/constructor/circuit/status already existed in the base dataset; only genuinely new entities got freshly minted sequential IDs):
  - 18 new drivers (rookies and reserve/test drivers who appeared in 2025-2026, e.g. Kimi Antonelli, Gabriel Bortoleto, Isack Hadjar, Arvid Lindblad)
  - 2 new constructors: **Audi** (Sauber's 2026 rebrand) and **Cadillac F1 Team** (new 2026 entrant)
  - 1 new circuit: **Madring** (Madrid street circuit, new for the 2026 calendar)
  - 2 new status codes: "Lapped" and "Did not start"

## What was intentionally NOT updated

- **`lap_times.csv` does not include 2025/2026 data.** Jolpica's lap-by-lap endpoint hit a sustained rate limit during this update; lap times were left as a follow-up to backfill in a separate, more slowly-paced run. Everything else (race results, qualifying, sprint results, pit stops, standings) is fully current through the Hungarian GP.
- Circuit **altitude** (`alt` column) is not exposed by the Jolpica API. The one new circuit (Madring) has `alt` set to `0` as a placeholder rather than a researched value.
- **`fastestLapSpeed` is `\N` for all 2025/2026 results.** Jolpica's `FastestLap` data no longer includes an average-speed field (only lap number and time), so this column can't be populated for the new rows.

## Methodology (for transparency / reproducibility)

1. Downloaded the base dataset via kagglehub.
2. Fetched every completed 2025/2026 race from Jolpica-F1 (`https://api.jolpi.ca/ergast/f1/`), caching raw JSON responses locally with request delays and retry/backoff to respect the API's rate limits.
3. Reconciled Jolpica's string refs (`driverRef`, `constructorRef`, `circuitRef`) and status text against the base dataset's existing integer IDs by exact match; only entities with no match in the base dataset were assigned new sequential IDs (logged for manual review before merging).
4. Appended new rows to each of the 14 base CSVs, preserving column order, dtypes, and the original dataset's `\N` null convention. Verified no duplicate primary keys and cross-checked foreign keys resolve correctly.
5. Spot-checked the most recent race's results against known standings before publishing.

## License

Same as the original dataset: **CC0: Public Domain**. This derivative work carries no additional restrictions.
