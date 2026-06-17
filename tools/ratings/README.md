# Monthly FIDE Progression Automation

This package generates the monthly **Performances** Pelican articles for [jeen-echecs.fr](https://www.jeen-echecs.fr) by comparing FIDE standard ratings at the start and end of each report month for JEEN club members.

## Layout

```
tools/ratings/
├── config.yaml              # club ref, federations, defaults
├── data/
│   ├── jeen_roster.csv      # committed club roster snapshot
│   └── fide_ratings.db      # local/CI cache (gitignored)
├── templates/progression.md.j2
└── ...
```

## Quick start

Install dependencies from the website repo root:

```bash
uv sync
```

Generate an article locally:

```bash
uv run python -m tools.ratings generate \
  --report-month 2026-02 \
  --publish-date 2026-03-02 \
  --top 5 \
  --output content/articles/
```

The command is idempotent: if the target article file already exists, generation is skipped.

## CLI commands

| Command | Purpose |
|---------|---------|
| `generate` | Build a Pelican article from the SQLite database and roster |
| `download --month mar26` | Download and load one FIDE monthly file |
| `load path/to/standard_mar26frl.txt` | Load a local FIDE text export |
| `bootstrap --months 24` | Seed the database with recent FIDE months |
| `refresh-roster --from-sqlite /path/to/Data.sqlite` | Export `jeen_roster.csv` from FFE data |

`generate` derives the FIDE publication month automatically from `--report-month`. For `2026-02`, ratings are compared on `2026-02-01` vs `2026-03-01` and the FIDE token is `mar26`.

## Roster maintenance

The monthly workflow reads the committed CSV only. Refresh it when club membership changes:

```bash
uv run python -m tools.ratings refresh-roster \
  --from-sqlite /path/to/chess_rating_stats/Data.sqlite
git add tools/ratings/data/jeen_roster.csv
git commit -m "chore: refresh JEEN FIDE roster"
```

Optional MDB conversion (requires `mdbtools`):

```bash
uv run python -m tools.ratings refresh-roster --from-mdb Data.mdb
```

Note: the FFE database is accessible on https://www.echecs.asso.fr/Papi/PapiData.zip

## GitHub Action

Workflow: [`.github/workflows/monthly-progression.yml`](../../.github/workflows/monthly-progression.yml)

- **Schedule**: `0 6 3 * *` UTC (3rd of each month)
- **Cache**: `tools/ratings/data/fide_ratings.db` under key `fide-ratings-db-v1`
- **On cache miss**: bootstraps the last 6 FIDE months, then continues
- **Commit**: pushes a new article to `main` when one is created

### Manual run (`workflow_dispatch`)

1. Open **Actions → Monthly Progression Article → Run workflow**
2. Optional inputs:
   - `report_month`: e.g. `2026-02`
   - `publish_date`: e.g. `2026-03-02`
   - `dry_run`: generate without committing
3. Inspect the workflow logs for the rendered article path

### Bootstrap the Actions cache

On the first automated run, the workflow rebuilds history by downloading recent FIDE files. To seed the cache from a local database instead:

1. Copy your existing `fide_ratings.db` to `tools/ratings/data/`
2. Run the workflow once via `workflow_dispatch`
3. The save-cache step persists the database for later runs

Alternatively, run locally:

```bash
uv run python -m tools.ratings bootstrap --months 24
```

Then commit nothing (the DB is gitignored) and upload/cache it through a manual workflow run on a branch that includes the file temporarily, or let the bootstrap step populate the cache on first CI run.

## Tests

```bash
uv sync --extra dev
uv run pytest
```

## Article conventions

- Title uses accented French month names (`février`, `août`, `décembre`)
- Filename uses unaccented slugs (`fevrier`, `aout`, `decembre`)
- Filename pattern: `YYYY-MM-DD Progression <month> <year>.md`
- New FIDE players appear in a congratulatory paragraph when a roster member has a rating at the end month but not the start month
