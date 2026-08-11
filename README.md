# F1 Dataset (1950-2026)

Scripts that build and maintain the [Formula 1 World Championship (1950-2026)](https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present) Kaggle dataset — an extension of the classic 1950-2020 F1 dataset with the full 2025 season and every completed 2026 race, kept current after every race weekend.

## What's here

- `scripts/` — the full pipeline: download the base dataset, fetch new race data from [Jolpica-F1](https://api.jolpi.ca/ergast/f1/), reconcile IDs against the existing dataset, merge, and fetch tire/weather/practice data via [FastF1](https://github.com/theOehrly/Fast-F1).
- `output/` — the 17 CSVs, README, SCHEMA.md, and CHANGELOG.md that get uploaded to Kaggle.
- `notebook/`, `notebook2/`, `notebook3/` — the example Kaggle notebooks published alongside the dataset.
- `update.sh` — run this after each race to update everything.

See [HOW_TO_UPDATE.md](HOW_TO_UPDATE.md) for the update workflow.

## Data source & structure

The dataset schema traces back to the [Ergast Developer API](http://ergast.com/mrd/) (retired 2024). New data since then comes from Jolpica-F1 (Ergast's maintained successor) for core race data, and FastF1 (official F1 live timing) for tire strategy, weather, and practice session data.

## Contributing

Issues and PRs welcome — especially around backfilling historical tire/weather data, improving fetch resilience, or adding new example notebooks.

## License

- **Data**: CC0: Public Domain.
- **Code** (this repo): MIT, see [LICENSE](LICENSE).
