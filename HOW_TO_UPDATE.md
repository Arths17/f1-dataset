# How to update the F1 dataset after a race

Run this from the project root:

```
./update.sh
```

## What it does

1. Fetches the latest completed race(s) from Jolpica-F1 (results, qualifying, sprint, pit stops, standings, and lap times).
2. Reconciles any new drivers/constructors/circuits/status codes against existing IDs.
3. Merges everything into the 14 core output CSVs in `output/`.
4. Fetches tire stint data (compound, stint length) for any new races via FastF1, rebuilding `tire_stints.csv`.
5. Runs an audit (schema, foreign keys, duplicates) and a validation pass (row counts, latest race check, spot-check).
6. Warns you if any brand-new entities showed up (new rookie, new team, etc.) so you can sanity-check names/spellings in `working/new_entities_log.csv` before publishing.

It does **not** push to Kaggle automatically. Review the output it prints, then push yourself:

```
cd output
kaggle datasets version -p . -m "Update through <race name>" -r zip
```

## If something looks off

- Check `working/new_entities_log.csv` for anything newly added — cross-check spellings against the real driver/team name.
- Re-run `python3 scripts/06_audit.py` and `python3 scripts/05_validate.py` from the project root for more detail.
- If a fetch fails partway (rate limiting), it's safe to just run `./update.sh` again — everything is cached and idempotent, so it picks up where it left off.
