"""Download and load FIDE standard rating list files into SQLite."""

from __future__ import annotations

import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PACKAGE_DIR / "data" / "fide_ratings.db"

COL_SPECS = [
    (0, 15),
    (15, 76),
    (76, 80),
    (80, 84),
    (84, 89),
    (89, 94),
    (94, 109),
    (109, 113),
    (113, 119),
    (119, 123),
    (123, 126),
    (126, 132),
    (132, 137),
]
COL_NAMES = [
    "id_number",
    "name",
    "fed",
    "sex",
    "tit",
    "wtit",
    "otit",
    "foa",
    "rating",
    "gms",
    "k",
    "b_day",
    "activity_flag",
]

FIDE_MONTH_TOKENS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def extract_date(line: str) -> str:
    """Extract rating list date from a FIDE header line (YYYY-MM-DD)."""
    date_str = line[113:119].strip()
    month_str = date_str[:3]
    year_str = date_str[3:]

    try:
        date_obj = datetime.strptime(month_str, "%b")
        return f"20{year_str}-{date_obj.month:02d}-01"
    except ValueError:
        return "0000-00-00"


def fide_token_for_date(year: int, month: int) -> str:
    """Build a FIDE download token such as ``mar26``."""
    return f"{FIDE_MONTH_TOKENS[month - 1]}{year % 100:02d}"


def end_month_to_fide_token(end_month: str) -> str:
    """Convert an end-month date string to a FIDE download token."""
    dt = datetime.strptime(end_month, "%Y-%m-%d")
    return fide_token_for_date(dt.year, dt.month)


def create_sqlite_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the FIDE ratings SQLite database if it does not exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fide_ratings (
            id_number TEXT,
            name TEXT,
            fed TEXT,
            sex TEXT,
            tit TEXT,
            wtit TEXT,
            otit TEXT,
            foa TEXT,
            rating INTEGER,
            date TEXT,
            gms INTEGER,
            k INTEGER,
            b_day TEXT,
            activity_flag TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_db_connection(database: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the FIDE ratings database."""
    return sqlite3.connect(database)


def load_file(filepath: str | Path, database: Path | str = DEFAULT_DB_PATH) -> bool:
    """
    Read a fixed-width FIDE rating file and append rows for its month.

    Returns True when new data was loaded, False when the month already exists.
    """
    filepath = Path(filepath)
    date = "0000-00-00"
    with filepath.open("r", encoding="latin-1") as handle:
        first_line = handle.readline()
        if first_line.startswith("ID"):
            date = extract_date(first_line)

    create_sqlite_db(database)
    conn = get_db_connection(database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM fide_ratings WHERE date = ? LIMIT 1",
        (date,),
    )
    if cursor.fetchone():
        print(f"Data for date {date} already exists. Skipping file {filepath}.")
        conn.close()
        return True

    try:
        frame = pd.read_fwf(
            filepath,
            colspecs=COL_SPECS,
            names=COL_NAMES,
            skiprows=1,
            encoding="latin-1",
            dtype={"id_number": str},
        )
        frame["date"] = date
        frame.to_sql("fide_ratings", conn, if_exists="append", index=False)
        print(f"Successfully loaded {len(frame)} records from {filepath} for date {date}.")
        return True
    except Exception as exc:
        print(f"Failed to load data from {filepath}. Error: {exc}")
        return False
    finally:
        conn.close()


def download_file(
    filename: str,
    download_dir: Path | str | None = None,
    max_retries: int = 1,
    retry_delay_seconds: int = 3600,
) -> Optional[Path]:
    """
    Download a FIDE rating zip, extract the text file, and return its path.

    ``filename`` is the token inside ``standard_{filename}frl.zip`` (e.g. ``mar26``).
    """
    import time

    url = f"http://ratings.fide.com/download/standard_{filename}frl.zip"
    download_dir = Path(download_dir or PACKAGE_DIR / "data")
    download_dir.mkdir(parents=True, exist_ok=True)
    zip_path = download_dir / "dl.zip"
    extracted_filename = download_dir / f"standard_{filename}frl.txt"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            zip_path.write_bytes(response.content)
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(download_dir)
            zip_path.unlink(missing_ok=True)
            return extracted_filename
        except requests.exceptions.RequestException as exc:
            print(f"Attempt {attempt}/{max_retries}: failed to download {url}. Error: {exc}")
            if attempt < max_retries:
                time.sleep(retry_delay_seconds)

    return None


def download_and_load(
    filename: str,
    database: Path | str = DEFAULT_DB_PATH,
    download_dir: Path | str | None = None,
    max_retries: int = 1,
    retry_delay_seconds: int = 3600,
) -> bool:
    """Download a FIDE file and load it into the database."""
    txt_path = download_file(
        filename,
        download_dir=download_dir,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )
    if txt_path is None:
        return False
    return load_file(txt_path, database=database)


def bootstrap_database(
    months: int = 12,
    database: Path | str = DEFAULT_DB_PATH,
    download_dir: Path | str | None = None,
) -> None:
    """Download and load the most recent ``months`` FIDE rating lists."""
    create_sqlite_db(database)
    today = datetime.today()
    year = today.year
    month = today.month

    for _ in range(months):
        token = fide_token_for_date(year, month)
        print(f"Bootstrapping FIDE list {token}...")
        download_and_load(token, database=database, download_dir=download_dir)
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
