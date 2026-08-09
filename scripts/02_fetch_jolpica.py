"""
Fetch 2025 and 2026 (through latest completed round) F1 data from the
Jolpica-F1 API (Ergast successor) and cache raw JSON responses locally.
"""
import json
import time
from datetime import date, datetime
from pathlib import Path

import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
RAW_DIR = Path(__file__).resolve().parent.parent / "working" / "raw_jolpica"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = [2025, 2026]
REQUEST_DELAY = 2.0
PAGE_LIMIT = 1000
TODAY = date.today()


def _cache_path(name: str) -> Path:
    return RAW_DIR / f"{name}.json"


def fetch(url_path: str, cache_name: str, paginate: bool = False) -> dict:
    """GET a Jolpica endpoint (optionally paginated), cache raw JSON, return merged MRData."""
    cache_file = _cache_path(cache_name)
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    all_data = None
    laps_by_number = {}  # lap number -> {"number": n, "Timings": {driverId: timing_dict}}
    offset = 0
    while True:
        sep = "&" if "?" in url_path else "?"
        url = f"{BASE_URL}/{url_path}{sep}limit={PAGE_LIMIT}&offset={offset}" if paginate else f"{BASE_URL}/{url_path}"

        for attempt in range(10):
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                break
            if resp.status_code == 429:
                wait = min(2 ** attempt, 30)
                print(f"  429 rate-limited on {url}, backing off {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                resp = None
                break
            resp.raise_for_status()
        else:
            raise RuntimeError(f"Failed after retries: {url}")

        time.sleep(REQUEST_DELAY)

        if resp is None:
            break

        payload = resp.json()
        mrdata = payload.get("MRData", {})

        table_key = next((k for k in mrdata if k.endswith("Table")), None)
        page_timing_count = 0
        is_laps = False
        if table_key:
            inner_list_key = next(k for k in mrdata[table_key] if isinstance(mrdata[table_key][k], list))
            inner_list = mrdata[table_key][inner_list_key]
            if inner_list_key == "Races" and inner_list and "Laps" in inner_list[0]:
                # laps.json paginates over individual Timing rows, which can split a lap
                # across page boundaries — merge by lap number, deduping by driverId.
                is_laps = True
                for lap in inner_list[0]["Laps"]:
                    num = lap["number"]
                    bucket = laps_by_number.setdefault(num, {"number": num, "Timings": {}})
                    for timing in lap["Timings"]:
                        bucket["Timings"][timing["driverId"]] = timing
                        page_timing_count += 1
            elif inner_list_key == "Races" and inner_list:
                nested_key = next((k for k in inner_list[0] if isinstance(inner_list[0][k], list)), None)
                page_size = len(inner_list[0][nested_key]) if nested_key else len(inner_list)
                if all_data is None:
                    all_data = payload
                else:
                    all_data["MRData"][table_key][inner_list_key][0][nested_key].extend(inner_list[0][nested_key])
                page_timing_count = page_size
            else:
                page_size = len(inner_list)
                if all_data is None:
                    all_data = payload
                else:
                    all_data["MRData"][table_key][inner_list_key].extend(inner_list)
                page_timing_count = page_size

        if all_data is None and is_laps:
            all_data = payload  # keep outer shell (Race metadata) from first page

        if not paginate:
            break

        total = int(mrdata.get("total", 0))
        if page_timing_count == 0:
            break
        offset += page_timing_count
        if offset >= total:
            break

    if all_data is None:
        all_data = {"MRData": {}}

    if laps_by_number:
        races = all_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if races:
            races[0]["Laps"] = [
                {"number": n, "Timings": list(laps_by_number[n]["Timings"].values())}
                for n in sorted(laps_by_number, key=int)
            ]

    cache_file.write_text(json.dumps(all_data))
    return all_data


def get_race_list(season: int) -> list[dict]:
    data = fetch(f"{season}/races.json", f"races_{season}")
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    return races


def is_completed(race: dict) -> bool:
    race_date = race.get("date")
    if not race_date:
        return False
    return datetime.strptime(race_date, "%Y-%m-%d").date() < TODAY


def main():
    summary = []

    for season in SEASONS:
        print(f"\n=== Season {season} ===")
        races = get_race_list(season)
        completed = [r for r in races if is_completed(r)]
        print(f"Total scheduled rounds: {len(races)}, completed: {len(completed)}")

        for race in completed:
            rnd = race["round"]
            race_name = race["raceName"]
            print(f"  Round {rnd}: {race_name} ({race['date']})")

            endpoints = [
                (f"{season}/{rnd}/results.json", f"results_{season}_{rnd}", False),
                (f"{season}/{rnd}/qualifying.json", f"qualifying_{season}_{rnd}", False),
                (f"{season}/{rnd}/sprint.json", f"sprint_{season}_{rnd}", False),
                (f"{season}/{rnd}/pitstops.json", f"pitstops_{season}_{rnd}", True),
                (f"{season}/{rnd}/driverStandings.json", f"driverStandings_{season}_{rnd}", False),
                (f"{season}/{rnd}/constructorStandings.json", f"constructorStandings_{season}_{rnd}", False),
            ]
            for url_path, cache_name, paginate in endpoints:
                try:
                    fetch(url_path, cache_name, paginate=paginate)
                except RuntimeError as e:
                    print(f"    FAILED (will retry on next run): {e}")

            summary.append((season, rnd, race_name, race["date"]))

        # circuits used this season (for new-circuit detection later)
        fetch(f"{season}/circuits.json", f"circuits_{season}")
        # full driver/constructor lists that appeared this season
        fetch(f"{season}/drivers.json", f"drivers_{season}")
        fetch(f"{season}/constructors.json", f"constructors_{season}")

    print("\n=== Fetch summary ===")
    for season, rnd, name, race_date in summary:
        print(f"  {season} R{rnd}: {name} — {race_date}")
    print(f"\nTotal completed races fetched: {len(summary)}")
    print(f"Raw JSON cached in: {RAW_DIR}")


if __name__ == "__main__":
    main()
