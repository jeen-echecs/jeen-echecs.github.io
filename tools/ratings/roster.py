"""Club roster loading and refresh helpers."""

from __future__ import annotations

import csv
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROSTER_PATH = PACKAGE_DIR / "data" / "jeen_roster.csv"

ROSTER_COLUMNS = ["fide_id", "first_name", "last_name"]


def normalize_fide_id(fide_id: str) -> str:
    """Strip leading zeros so FFE exports match FIDE rating list IDs."""
    fide_id = str(fide_id).strip()
    if fide_id.isdigit():
        return str(int(fide_id))
    return fide_id


def load_roster(path: Path | str = DEFAULT_ROSTER_PATH) -> pd.DataFrame:
    """Load the committed JEEN roster CSV."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Roster file not found: {path}")

    frame = pd.read_csv(path, dtype={"fide_id": str})
    missing = set(ROSTER_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Roster file missing columns: {sorted(missing)}")
    frame["fide_id"] = frame["fide_id"].map(normalize_fide_id)
    return frame[ROSTER_COLUMNS]


def save_roster(frame: pd.DataFrame, path: Path | str = DEFAULT_ROSTER_PATH) -> Path:
    """Write roster rows to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    output = frame[ROSTER_COLUMNS].copy()
    output["fide_id"] = output["fide_id"].map(normalize_fide_id)
    output = output.sort_values(["last_name", "first_name"])
    output.to_csv(path, index=False)
    return path


def export_roster_from_sqlite(
    sqlite_path: Path | str,
    club_ref: int,
    output_path: Path | str = DEFAULT_ROSTER_PATH,
) -> pd.DataFrame:
    """Export JEEN members with a FIDE code from an FFE SQLite database."""
    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    query = (
        "SELECT FideCode AS fide_id, Prenom AS first_name, Nom AS last_name "
        "FROM JOUEUR "
        "WHERE CAST(ClubRef AS INTEGER) = ? "
        "AND FideCode IS NOT NULL AND TRIM(FideCode) != '' "
        "ORDER BY Nom, Prenom"
    )
    with sqlite3.connect(sqlite_path) as conn:
        frame = pd.read_sql_query(query, conn, params=(club_ref,))

    if frame.empty:
        raise ValueError(f"No roster rows found for ClubRef={club_ref} in {sqlite_path}")

    frame["fide_id"] = frame["fide_id"].map(normalize_fide_id)
    frame["first_name"] = frame["first_name"].astype(str).str.strip()
    frame["last_name"] = frame["last_name"].astype(str).str.strip()
    save_roster(frame, output_path)
    print(f"Exported {len(frame)} roster rows to {output_path}")
    return frame


def convert_mdb_to_sqlite(mdb_path: Path | str) -> Path:
    """
    Convert an FFE Access database to SQLite using mdbtools.

    Requires ``mdb-tables`` and ``mdb-export`` on PATH.
    """
    mdb_path = Path(mdb_path)
    sqlite_path = mdb_path.with_suffix(".sqlite")

    if sqlite_path.exists():
        sqlite_path.unlink()

    conn = sqlite3.connect(sqlite_path)
    conn.close()

    result = subprocess.run(
        ["mdb-tables", str(mdb_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    tables = result.stdout.split()

    for table in tables:
        csv_path = Path(f"{table}.csv")
        with csv_path.open("w", encoding="utf-8", newline="") as outfile:
            subprocess.run(
                ["mdb-export", "-d", "|", str(mdb_path), table],
                stdout=outfile,
                check=True,
            )

        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter="|")
            header = next(reader)
            header = [col.strip('"') or f"column{i}" for i, col in enumerate(header)]
            placeholders = ",".join(["?"] * len(header))

            with sqlite3.connect(sqlite_path) as conn:
                cursor = conn.cursor()
                create_sql = (
                    f"CREATE TABLE IF NOT EXISTS {table} "
                    f"({', '.join(f'{col} TEXT' for col in header)})"
                )
                cursor.execute(create_sql)
                insert_sql = f"INSERT INTO {table} ({', '.join(header)}) VALUES ({placeholders})"
                for row in reader:
                    values = [value.strip('"') for value in row]
                    if values:
                        cursor.execute(insert_sql, values)
                conn.commit()

        csv_path.unlink(missing_ok=True)

    print(f"Converted {mdb_path} to {sqlite_path}")
    return sqlite_path


def refresh_roster_from_mdb(
    mdb_path: Path | str,
    club_ref: int,
    output_path: Path | str = DEFAULT_ROSTER_PATH,
) -> pd.DataFrame:
    """Convert MDB to SQLite and export the club roster."""
    sqlite_path = convert_mdb_to_sqlite(mdb_path)
    return export_roster_from_sqlite(sqlite_path, club_ref, output_path)
