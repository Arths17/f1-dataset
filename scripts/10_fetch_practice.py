"""
Build practice_results.csv for the 2025-2026 races using FastF1: one row
per driver per practice session (FP1/FP2/FP3), with best lap time, laps
completed, and rank. Drivers who only appear in practice (reserve/test
drivers not in drivers.csv) are skipped with a warning - they didn't race
so aren't part of the existing dataset's driver lookup.
"""
import time
from pathlib import Path

import fastf1
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "working" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

OUT_DIR = ROOT / "output"
BASE_RACES = pd.read_csv(OUT_DIR / "races.csv")
DRIVERS = pd.read_csv(OUT_DIR / "drivers.csv")
code_to_id = dict(zip(DRIVERS["code"].dropna(), DRIVERS["driverId"]))

SEASONS = [2025, 2026]
SESSIONS = ["FP1", "FP2", "FP3"]


def get_completed_rounds(season):
    rows = BASE_RACES[BASE_RACES.year == season]
    return sorted(rows["round"].tolist())


def main():
    existing_path = OUT_DIR / "practice_results.csv"
    existing = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame(columns=["raceId"])
    already_done = set(existing["raceId"])

    rows = []
    failures = []
    skipped_drivers = set()

    for season in SEASONS:
        for rnd in get_completed_rounds(season):
            race_id = BASE_RACES[(BASE_RACES.year == season) & (BASE_RACES["round"] == rnd)]["raceId"].iloc[0]
            if race_id in already_done:
                continue
            for sess_name in SESSIONS:
                print(f"{season} round {rnd} {sess_name} (raceId {race_id})...")
                try:
                    session = fastf1.get_session(season, rnd, sess_name)
                    session.load(laps=True, telemetry=False, weather=False, messages=False)
                except Exception as e:
                    print(f"  no session or failed to load: {e}")
                    failures.append((season, rnd, sess_name, str(e)))
                    continue

                laps = session.laps
                if laps is None or laps.empty:
                    continue

                best = laps.groupby("Driver")["LapTime"].min().dropna().sort_values()
                lap_counts = laps.groupby("Driver").size()

                mapped = [(code, t) for code, t in best.items() if code_to_id.get(code) is not None]
                for code, _ in best.items():
                    if code_to_id.get(code) is None:
                        skipped_drivers.add(code)

                for rank, (driver_code, best_time) in enumerate(mapped, start=1):
                    driver_id = code_to_id[driver_code]
                    rows.append({
                        "raceId": int(race_id),
                        "driverId": int(driver_id),
                        "session": sess_name,
                        "position": rank,
                        "bestLapTime": str(best_time),
                        "laps": int(lap_counts.get(driver_code, 0)),
                    })
                time.sleep(1)

    new_df = pd.DataFrame(rows)
    df = pd.concat([existing, new_df], ignore_index=True)
    df = df.drop_duplicates(subset=["raceId", "driverId", "session"]).sort_values(["raceId", "session", "position"])
    df.to_csv(OUT_DIR / "practice_results.csv", index=False)
    print(f"\nAdded {len(new_df)} new practice-result rows, {len(df)} total, written to {OUT_DIR / 'practice_results.csv'}")
    if skipped_drivers:
        print(f"\nSkipped {len(skipped_drivers)} driver codes not in drivers.csv (reserve/test drivers, practice-only): {sorted(skipped_drivers)}")
    if failures:
        print(f"\n{len(failures)} sessions failed/missing:")
        for season, rnd, sess_name, err in failures:
            print(f"  {season} round {rnd} {sess_name}: {err}")


if __name__ == "__main__":
    main()
