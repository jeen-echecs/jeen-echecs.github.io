from datetime import date

import pandas as pd
import pytest

from tools.ratings.article import render_article
from tools.ratings.fide_etl import extract_date, end_month_to_fide_token
from tools.ratings.performance import (
    calculate_monthly_improvements,
    detect_new_fide_players,
    report_month_to_period,
)


HEADER = (
    "ID Number      Name                                                         Fed Sex Tit  WTit OTit           FOA FEB26 Gms K  B-day Flag\n"
)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (HEADER, "2026-02-01"),
        (
            "ID Number      Name                                                         Fed Sex Tit  WTit OTit           FOA MAR26 Gms K  B-day Flag\n",
            "2026-03-01",
        ),
        (
            "ID Number      Name                                                         Fed Sex Tit  WTit OTit           FOA DEC25 Gms K  B-day Flag\n",
            "2025-12-01",
        ),
    ],
)
def test_extract_date(line, expected):
    assert extract_date(line) == expected


def test_report_month_to_period():
    period = report_month_to_period("2026-02")
    assert period.start_month == "2026-02-01"
    assert period.end_month == "2026-03-01"
    assert period.fide_token == "mar26"
    assert period.month_name_fr == "février"
    assert period.month_slug == "fevrier"


def test_end_month_to_fide_token():
    assert end_month_to_fide_token("2026-03-01") == "mar26"


def test_calculate_monthly_improvements_pivot():
    frame = pd.DataFrame(
        [
            {"id_number": "1", "name": "Alpha, Alice", "fed": "FRA", "rating": 1500, "date": "2026-02-01"},
            {"id_number": "1", "name": "Alpha, Alice", "fed": "FRA", "rating": 1550, "date": "2026-03-01"},
            {"id_number": "2", "name": "Beta, Bob", "fed": "FRA", "rating": 1600, "date": "2026-02-01"},
            {"id_number": "2", "name": "Beta, Bob", "fed": "FRA", "rating": 1590, "date": "2026-03-01"},
            {"id_number": "3", "name": "Gamma, Gail", "fed": "FRA", "rating": 1400, "date": "2026-02-01"},
            {"id_number": "3", "name": "Gamma, Gail", "fed": "FRA", "rating": 1450, "date": "2026-03-01"},
        ]
    )
    roster = pd.DataFrame(
        {
            "fide_id": ["1", "2", "3"],
            "first_name": ["Alice", "Bob", "Gail"],
            "last_name": ["Alpha", "Beta", "Gamma"],
        }
    )

    performers = calculate_monthly_improvements(
        frame,
        roster,
        "2026-02-01",
        "2026-03-01",
    )

    assert [row["name"] for row in performers] == ["Alpha, Alice", "Gamma, Gail"]
    assert performers[0]["progression"] == 50
    assert performers[1]["progression"] == 50


def test_roster_leading_zero_fide_ids():
    frame = pd.DataFrame(
        [
            {"id_number": "611000", "name": "Kozlowski, Thierry", "fed": "FRA", "rating": 1994, "date": "2026-02-01"},
            {"id_number": "611000", "name": "Kozlowski, Thierry", "fed": "FRA", "rating": 2016, "date": "2026-03-01"},
        ]
    )
    roster = pd.DataFrame(
        {
            "fide_id": ["00611000"],
            "first_name": ["Thierry"],
            "last_name": ["KOZLOWSKI"],
        }
    )

    performers = calculate_monthly_improvements(
        frame,
        roster,
        "2026-02-01",
        "2026-03-01",
    )

    assert len(performers) == 1
    assert performers[0]["name"] == "Kozlowski, Thierry"
    assert performers[0]["progression"] == 22


def test_detect_new_fide_players():
    frame = pd.DataFrame(
        [
            {"id_number": "10", "name": "Old, Player", "fed": "FRA", "rating": 1500, "date": "2026-02-01"},
            {"id_number": "10", "name": "Old, Player", "fed": "FRA", "rating": 1510, "date": "2026-03-01"},
            {"id_number": "20", "name": "Fresh, Face", "fed": "FRA", "rating": 1537, "date": "2026-03-01"},
        ]
    )
    roster = pd.DataFrame(
        {
            "fide_id": ["10", "20"],
            "first_name": ["Player", "Hugo"],
            "last_name": ["Old", "Fresh"],
        }
    )

    new_players = detect_new_fide_players(frame, roster, "2026-02-01", "2026-03-01")
    assert new_players == [{"first_name": "Hugo", "rating": 1537}]


def test_render_article_template():
    period = report_month_to_period("2026-02")
    performers = [
        {
            "name": "Hwang, Darby",
            "old_rating": 1474,
            "new_rating": 1518,
            "progression": 44,
        }
    ]
    content = render_article(
        period,
        "2026-03-02",
        performers,
        [],
        top_n=4,
    )

    assert "Title: Performances février 2026" in content
    assert "Date: 2026-03-02" in content
    assert "| Hwang, Darby              | 1474            | 1518        | 44          |" in content
    assert "4\u202fplus belles progressions" in content
    assert "premier elo FIDE" not in content


def test_render_article_with_new_players():
    period = report_month_to_period("2025-04")
    content = render_article(
        period,
        "2025-05-16",
        [],
        [{"first_name": "Hugo", "rating": 1537}, {"first_name": "Théodore", "rating": 1468}],
        top_n=5,
    )

    assert "**Hugo (1537)** et **Théodore (1468)**" in content
    assert "premier elo FIDE officiel" in content
