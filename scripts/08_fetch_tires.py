"""
Build tire_stints.csv for the 2025-2026 races using FastF1 (pulls from the
official F1 live timing feed). One row per driver per stint: compound,
start/end lap, and stint length. Historical (pre-2025) tire data isn't in
scope here - this only covers the same 35 races already extended.
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


def get_completed_rounds(season):
    rows = BASE_RACES[BASE_RACES.year == season]
    return sorted(rows["round"].tolist())


def main():
    existing_path = OUT_DIR / "tire_stints.csv"
    existing = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame(columns=["raceId"])
    already_done = set(existing["raceId"])

    stint_rows = []
    failures = []

    for season in SEASONS:
        for rnd in get_completed_rounds(season):
            race_id = BASE_RACES[(BASE_RACES.year == season) & (BASE_RACES["round"] == rnd)]["raceId"].iloc[0]
            if race_id in already_done:
                continue
            print(f"{season} round {rnd} (raceId {race_id})...")
            try:
                session = fastf1.get_session(season, rnd, "R")
                session.load(laps=True, telemetry=False, weather=False, messages=False)
            except Exception as e:
                print(f"  FAILED to load session: {e}")
                failures.append((season, rnd, str(e)))
                continue

            laps = session.laps
            for (driver_code, stint_num), grp in laps.groupby(["Driver", "Stint"]):
                if pd.isna(stint_num):
                    continue
                driver_id = code_to_id.get(driver_code)
                if driver_id is None:
                    print(f"  no driverId mapping for code {driver_code}, skipping")
                    continue
                valid_compounds = grp["Compound"].dropna()
                valid_compounds = valid_compounds[valid_compounds != "None"]
                compound = valid_compounds.iloc[0] if len(valid_compounds) else "\\N"
                start_lap = int(grp["LapNumber"].min())
                end_lap = int(grp["LapNumber"].max())
                stint_rows.append({
                    "raceId": int(race_id),
                    "driverId": int(driver_id),
                    "stint": int(stint_num),
                    "compound": compound,
                    "startLap": start_lap,
                    "endLap": end_lap,
                    "lapsOnTire": end_lap - start_lap + 1,
                })
            time.sleep(1)

    new_df = pd.DataFrame(stint_rows)
    df = pd.concat([existing, new_df], ignore_index=True)
    df = df.drop_duplicates(subset=["raceId", "driverId", "stint"]).sort_values(["raceId", "driverId", "stint"])
    df.to_csv(OUT_DIR / "tire_stints.csv", index=False)
    print(f"\nAdded {len(new_df)} new stint rows, {len(df)} total, written to {OUT_DIR / 'tire_stints.csv'}")
    if failures:
        print(f"\n{len(failures)} races failed to load:")
        for season, rnd, err in failures:
            print(f"  {season} round {rnd}: {err}")


if __name__ == "__main__":
    main()
