#!/bin/bash
# Full update pipeline: fetch latest completed race(s), reconcile IDs, merge,
# validate, and (if you approve) push a new Kaggle dataset version.
set -e
cd "$(dirname "$0")/.."

echo "=== 1. Fetching latest race data (races/results/qualifying/sprint/pitstops/standings) ==="
python3 scripts/02_fetch_jolpica.py

echo
echo "=== 2. Fetching lap times for any new races (slow, race-by-race) ==="
python3 scripts/07_fetch_laps.py

echo
echo "=== 3. Reconciling driver/constructor/circuit/status IDs ==="
cp -f working/new_entities_log.csv working/new_entities_log.prev.csv 2>/dev/null || true
python3 scripts/03_reconcile_ids.py

echo
echo "=== 4. Merging into output CSVs ==="
python3 scripts/04_merge.py

echo
echo "=== 5. Fetching tire stint data for any new races (via FastF1) ==="
python3 scripts/08_fetch_tires.py

echo
echo "=== 6. Fetching weather data for any new races (via FastF1) ==="
python3 scripts/09_fetch_weather.py

echo
echo "=== 7. Fetching practice session results for any new races (via FastF1) ==="
python3 scripts/10_fetch_practice.py

echo
echo "=== 8. Auditing schema/FK/duplicate integrity ==="
python3 scripts/06_audit.py

echo
echo "=== 9. Validating row counts and latest race ==="
python3 scripts/05_validate.py

echo
if ! diff -q working/new_entities_log.prev.csv working/new_entities_log.csv > /dev/null 2>&1; then
    echo "!!! NEW ENTITIES DETECTED since last run - review working/new_entities_log.csv before pushing !!!"
    diff working/new_entities_log.prev.csv working/new_entities_log.csv || true
else
    echo "No new entities since last run."
fi

echo
echo "=== Done. Review the output above, then push with: ==="
echo "  cd output && kaggle datasets version -p . -m \"Update through <race name>\" -r zip"
