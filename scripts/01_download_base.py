import shutil
from pathlib import Path

import kagglehub
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent / "working" / "base"
BASE_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "circuits.csv",
    "constructor_results.csv",
    "constructor_standings.csv",
    "constructors.csv",
    "driver_standings.csv",
    "drivers.csv",
    "lap_times.csv",
    "pit_stops.csv",
    "qualifying.csv",
    "races.csv",
    "results.csv",
    "seasons.csv",
    "sprint_results.csv",
    "status.csv",
]


def main():
    path = kagglehub.dataset_download("rohanrao/formula-1-world-championship-1950-2020")
    src_dir = Path(path)
    print(f"Downloaded dataset to cache: {src_dir}\n")

    for fname in FILES:
        src = src_dir / fname
        dst = BASE_DIR / fname
        shutil.copy2(src, dst)

    print(f"Copied {len(FILES)} CSVs to {BASE_DIR}\n")
    print("=" * 80)

    for fname in FILES:
        fpath = BASE_DIR / fname
        df = pd.read_csv(fpath, low_memory=False)
        print(f"\n### {fname}  ({len(df):,} rows, {len(df.columns)} columns)")
        print("-" * 80)
        for col, dtype in df.dtypes.items():
            print(f"  {col:<20} {dtype}")


if __name__ == "__main__":
    main()
