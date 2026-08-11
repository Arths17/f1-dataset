"""
Backfill lap_times for the 2025/2026 races, one race at a time with a
generous pause between races to avoid the sustained rate-limiting hit
during the original bulk attempt.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

fetch_mod = import_module("02_fetch_jolpica")

PAUSE_BETWEEN_RACES = 8  # seconds


def main():
    for season in fetch_mod.SEASONS:
        races = fetch_mod.get_race_list(season)
        completed = [r for r in races if fetch_mod.is_completed(r)]
        print(f"=== Season {season}: {len(completed)} completed races ===")

        for race in completed:
            rnd = race["round"]
            cache_name = f"laps_{season}_{rnd}"
            cache_file = fetch_mod._cache_path(cache_name)
            if cache_file.exists():
                print(f"  Round {rnd}: already cached, skipping")
                continue

            print(f"  Round {rnd}: {race['raceName']} - fetching laps...")
            try:
                fetch_mod.fetch(f"{season}/{rnd}/laps.json", cache_name, paginate=True)
                print(f"    done")
            except RuntimeError as e:
                print(f"    FAILED: {e}")

            time.sleep(PAUSE_BETWEEN_RACES)


if __name__ == "__main__":
    main()
