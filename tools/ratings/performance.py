"""Monthly rating progression calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import pandas as pd

from .fide_etl import end_month_to_fide_token
from .roster import normalize_fide_id


MONTHS_FR = {
    1: ("janvier", "janvier"),
    2: ("février", "fevrier"),
    3: ("mars", "mars"),
    4: ("avril", "avril"),
    5: ("mai", "mai"),
    6: ("juin", "juin"),
    7: ("juillet", "juillet"),
    8: ("août", "aout"),
    9: ("septembre", "septembre"),
    10: ("octobre", "octobre"),
    11: ("novembre", "novembre"),
    12: ("décembre", "decembre"),
}


@dataclass(frozen=True)
class ReportPeriod:
    report_month: str
    start_month: str
    end_month: str
    year: int
    month: int
    month_name_fr: str
    month_slug: str
    fide_token: str


def report_month_to_period(report_month: str) -> ReportPeriod:
    """Derive start/end month dates and labels from ``YYYY-MM``."""
    year_str, month_str = report_month.split("-")
    year = int(year_str)
    month = int(month_str)
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    month_name_fr, month_slug = MONTHS_FR[month]
    start_month = start.isoformat()
    end_month = end.isoformat()

    return ReportPeriod(
        report_month=report_month,
        start_month=start_month,
        end_month=end_month,
        year=year,
        month=month,
        month_name_fr=month_name_fr,
        month_slug=month_slug,
        fide_token=end_month_to_fide_token(end_month),
    )


def load_fide_frame(
    conn,
    federations: Iterable[str],
) -> pd.DataFrame:
    """Load FIDE ratings for selected federations from SQLite."""
    placeholders = ", ".join("?" for _ in federations)
    query = (
        f"SELECT id_number, name, fed, rating, date "
        f"FROM fide_ratings WHERE fed IN ({placeholders}) ORDER BY date"
    )
    frame = pd.read_sql_query(query, conn, params=list(federations))
    if frame.empty:
        return frame

    frame["id_number"] = frame["id_number"].astype(str).map(
        lambda value: normalize_fide_id(value) if value else value
    )
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    return frame


def calculate_monthly_improvements(
    fide_players_df: pd.DataFrame,
    roster_df: pd.DataFrame,
    start_month: str,
    end_month: str,
) -> list[dict]:
    """
    Compute positive rating deltas between exact start/end month snapshots.

    Groups by FIDE id_number and compares ratings on the two month boundaries.
    """
    if fide_players_df.empty or roster_df.empty:
        return []

    roster_ids = set(roster_df["fide_id"].astype(str).map(normalize_fide_id))
    start_rows = (
        fide_players_df[fide_players_df["date"] == start_month]
        .drop_duplicates("id_number")
        .set_index("id_number")
    )
    end_rows = (
        fide_players_df[fide_players_df["date"] == end_month]
        .drop_duplicates("id_number")
        .set_index("id_number")
    )

    common_ids = start_rows.index.intersection(end_rows.index)
    diff = end_rows.loc[common_ids, "rating"] - start_rows.loc[common_ids, "rating"]
    positive = diff[diff > 0].sort_values(ascending=False)

    performers: list[dict] = []
    for fide_id, progression in positive.items():
        if fide_id not in roster_ids:
            continue
        performers.append(
            {
                "name": str(end_rows.loc[fide_id, "name"]).strip(),
                "old_rating": int(start_rows.loc[fide_id, "rating"]),
                "new_rating": int(end_rows.loc[fide_id, "rating"]),
                "progression": int(progression),
            }
        )
    return performers


def detect_new_fide_players(
    fide_players_df: pd.DataFrame,
    roster_df: pd.DataFrame,
    start_month: str,
    end_month: str,
) -> list[dict]:
    """
    Find club roster members with a rating at end_month but none at start_month.
    """
    if fide_players_df.empty or roster_df.empty:
        return []

    start_ids = set(
        fide_players_df[fide_players_df["date"] == start_month]["id_number"].astype(str)
    )
    end_rows = (
        fide_players_df[fide_players_df["date"] == end_month]
        .drop_duplicates("id_number")
        .set_index("id_number")
    )

    new_players: list[dict] = []
    for _, roster_row in roster_df.iterrows():
        fide_id = normalize_fide_id(str(roster_row["fide_id"]))
        if fide_id in start_ids or fide_id not in end_rows.index:
            continue
        new_players.append(
            {
                "first_name": str(roster_row["first_name"]).strip(),
                "rating": int(end_rows.loc[fide_id, "rating"]),
            }
        )

    return sorted(new_players, key=lambda player: -player["rating"])
