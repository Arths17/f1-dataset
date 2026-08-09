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

print("=== 1. Column order & dtype diff vs base ===")
issues = 0
for f in FILES:
    base = pd.read_csv(BASE_DIR / f, low_memory=False)
    out = pd.read_csv(OUT_DIR / f, low_memory=False)
    if list(base.columns) != list(out.columns):
        print(f"  {f}: COLUMN ORDER MISMATCH  base={list(base.columns)}  out={list(out.columns)}")
        issues += 1
        continue
    for col in base.columns:
        if base[col].dtype != out[col].dtype:
            print(f"  {f}.{col}: dtype changed {base[col].dtype} -> {out[col].dtype}")
            issues += 1
print(f"  ({issues} issues)" if issues else "  OK — all columns/dtypes match base")

print("\n=== 2. Foreign key integrity (new rows only) ===")
circuits = pd.read_csv(OUT_DIR / "circuits.csv")
drivers = pd.read_csv(OUT_DIR / "drivers.csv")
constructors = pd.read_csv(OUT_DIR / "constructors.csv")
races = pd.read_csv(OUT_DIR / "races.csv")
status = pd.read_csv(OUT_DIR / "status.csv")

valid_circuit_ids = set(circuits.circuitId)
valid_driver_ids = set(drivers.driverId)
valid_constructor_ids = set(constructors.constructorId)
valid_race_ids = set(races.raceId)
valid_status_ids = set(status.statusId)

bad_race_circuits = races[~races.circuitId.isin(valid_circuit_ids)]
print(f"  races.circuitId not in circuits: {len(bad_race_circuits)}")

for f, cols in [
    ("results.csv", ["raceId", "driverId", "constructorId"]),
    ("qualifying.csv", ["raceId", "driverId", "constructorId"]),
    ("sprint_results.csv", ["raceId", "driverId", "constructorId"]),
    ("pit_stops.csv", ["raceId", "driverId"]),
    ("driver_standings.csv", ["raceId", "driverId"]),
    ("constructor_standings.csv", ["raceId", "constructorId"]),
    ("constructor_results.csv", ["raceId", "constructorId"]),
]:
    df = pd.read_csv(OUT_DIR / f, low_memory=False)
    for col in cols:
        ref = {"raceId": valid_race_ids, "driverId": valid_driver_ids, "constructorId": valid_constructor_ids}[col]
        bad = df[~df[col].isin(ref)]
        if len(bad):
            print(f"  {f}.{col}: {len(bad)} rows reference missing IDs -- e.g. {bad[col].unique()[:5]}")

results = pd.read_csv(OUT_DIR / "results.csv", low_memory=False)
bad_status = results[~results.statusId.isin(valid_status_ids)]
print(f"  results.statusId not in status: {len(bad_status)}")
sprint = pd.read_csv(OUT_DIR / "sprint_results.csv", low_memory=False)
bad_status_sprint = sprint[~sprint.statusId.isin(valid_status_ids)]
print(f"  sprint_results.statusId not in status: {len(bad_status_sprint)}")

print("\n=== 3. Null-marker consistency (\\N usage in new rows) ===")
base_results = pd.read_csv(BASE_DIR / "results.csv", low_memory=False)
new_results = results[results.resultId > base_results.resultId.max()]
for col in ["number", "position", "time", "milliseconds", "fastestLap", "rank", "fastestLapTime", "fastestLapSpeed"]:
    n_na = (new_results[col].astype(str) == "\\N").sum()
    n_empty = (new_results[col].astype(str) == "").sum()
    n_nan = new_results[col].isna().sum()
    print(f"  results.{col}: \\N={n_na}, empty-string={n_empty}, actual-NaN={n_nan}")

print("\n=== 4. Duplicate row check (exact duplicate rows) ===")
for f in FILES:
    df = pd.read_csv(OUT_DIR / f, low_memory=False)
    dupes = df.duplicated().sum()
    if dupes:
        print(f"  {f}: {dupes} fully-duplicate rows")
print("  (none reported above = clean)")

print("\n=== 5. File size sanity ===")
total_size = sum((OUT_DIR / f).stat().st_size for f in FILES)
print(f"  Total CSV size: {total_size / 1e6:.1f} MB")
print(f"  lap_times.csv: {(OUT_DIR / 'lap_times.csv').stat().st_size / 1e6:.1f} MB (largest, unchanged from base)")

print("\n=== 6. dataset-metadata.json validity ===")
import json
meta = json.loads((OUT_DIR / "dataset-metadata.json").read_text())
required = {"title", "id", "licenses"}
missing = required - meta.keys()
print(f"  Missing required fields: {missing}" if missing else "  All required fields present")
print(f"  id: {meta['id']}  (must be lowercase/hyphen, no spaces)")
print(f"  id valid format: {meta['id'].replace('-', '').replace('_','').replace('/','').isalnum() and meta['id'] == meta['id'].lower()}")
