"""
Build weather.csv for the 2025-2026 races using FastF1 (official F1 live
timing weather feed). One row per race: aggregated air/track temperature,
humidity, wind, and whether it rained during the session.
"""
import time
from datetime import date
from pathlib import Path

import fastf1
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "working" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

OUT_DIR = ROOT / "output"
BASE_RACES = pd.read_csv(OUT_DIR / "races.csv")

SEASONS = list(range(2025, date.today().year + 1))


def get_completed_rounds(season):
    rows = BASE_RACES[BASE_RACES.year == season]
    return sorted(rows["round"].tolist())


def main():
    existing_path = OUT_DIR / "weather.csv"
    existing = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame(columns=["raceId"])
    already_done = set(existing["raceId"])

    weather_rows = []
    failures = []

    for season in SEASONS:
        for rnd in get_completed_rounds(season):
            race_id = BASE_RACES[(BASE_RACES.year == season) & (BASE_RACES["round"] == rnd)]["raceId"].iloc[0]
            if race_id in already_done:
                continue
            print(f"{season} round {rnd} (raceId {race_id})...")
            try:
                session = fastf1.get_session(season, rnd, "R")
                session.load(laps=False, telemetry=False, weather=True, messages=False)
            except Exception as e:
                print(f"  FAILED to load session: {e}")
                failures.append((season, rnd, str(e)))
                continue

            w = session.weather_data
            if w is None or w.empty:
                print("  no weather data available")
                continue

            weather_rows.append({
                "raceId": int(race_id),
                "airTempAvg": round(w["AirTemp"].mean(), 1),
                "airTempMin": round(w["AirTemp"].min(), 1),
                "airTempMax": round(w["AirTemp"].max(), 1),
                "trackTempAvg": round(w["TrackTemp"].mean(), 1),
                "trackTempMin": round(w["TrackTemp"].min(), 1),
                "trackTempMax": round(w["TrackTemp"].max(), 1),
                "humidityAvg": round(w["Humidity"].mean(), 1),
                "windSpeedAvg": round(w["WindSpeed"].mean(), 1),
                "windSpeedMax": round(w["WindSpeed"].max(), 1),
                "rainfall": bool(w["Rainfall"].any()),
            })
            time.sleep(1)

    new_df = pd.DataFrame(weather_rows)
    df = pd.concat([existing, new_df], ignore_index=True).drop_duplicates(subset="raceId").sort_values("raceId")
    df.to_csv(OUT_DIR / "weather.csv", index=False)
    print(f"\nAdded {len(new_df)} new race-weather rows, {len(df)} total, written to {OUT_DIR / 'weather.csv'}")
    if failures:
        print(f"\n{len(failures)} races failed to load:")
        for season, rnd, err in failures:
            print(f"  {season} round {rnd}: {err}")


if __name__ == "__main__":
    main()
