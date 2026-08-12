import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT / "working" / "base"
OUT_DIR = ROOT / "output"

FILES = [
    "circuits.csv", "constructor_results.csv", "constructor_standings.csv",
    "constructors.csv", "driver_standings.csv", "drivers.csv", "lap_times.csv",
    "pit_stops.csv", "qualifying.csv", "races.csv", "results.csv", "seasons.csv",
    "sprint_results.csv", "status.csv",
]

print("=== Before/after row counts ===")
for f in FILES:
    before = sum(1 for _ in open(BASE_DIR / f)) - 1
    after = sum(1 for _ in open(OUT_DIR / f)) - 1
    flag = "" if after >= before else "  <-- SHRUNK, INVESTIGATE"
    print(f"  {f:<28} {before:>7} -> {after:>7}  (+{after - before}){flag}")

races = pd.read_csv(OUT_DIR / "races.csv")
print(f"\nTotal races: {len(races)}")
for yr, count in races[races.year >= 2025].groupby("year").size().items():
    print(f"{yr} races: {count}")
races["date"] = pd.to_datetime(races["date"])
latest = races.sort_values("date").iloc[-1]
print(f"Most recent race: {latest['name']} on {latest['date'].date()} (round {latest['round']}, {latest['year']})")

print("\n=== Duplicate primary key checks ===")
pk_map = {
    "circuits.csv": "circuitId", "constructors.csv": "constructorId",
    "drivers.csv": "driverId", "races.csv": "raceId", "results.csv": "resultId",
    "qualifying.csv": "qualifyId", "sprint_results.csv": "resultId",
    "status.csv": "statusId", "constructor_results.csv": "constructorResultsId",
    "constructor_standings.csv": "constructorStandingsId",
    "driver_standings.csv": "driverStandingsId",
}
for f, pk in pk_map.items():
    df = pd.read_csv(OUT_DIR / f)
    dupes = df[pk].duplicated().sum()
    status = "OK" if dupes == 0 else f"DUPLICATES: {dupes}"
    print(f"  {f:<28} pk={pk:<24} {status}")

print(f"\n=== Spot check: most recent race ({latest['name']} {latest['date'].date()}) results ===")
race_id = latest["raceId"]
results = pd.read_csv(OUT_DIR / "results.csv")
drivers = pd.read_csv(OUT_DIR / "drivers.csv")
top5 = results[results.raceId == race_id].sort_values("positionOrder").head(5)
top5 = top5.merge(drivers[["driverId", "forename", "surname"]], on="driverId")
print(top5[["positionOrder", "forename", "surname", "points", "grid", "statusId"]].to_string(index=False))

print("\n=== New entities recap ===")
print(open(ROOT / "working" / "new_entities_log.csv").read())
