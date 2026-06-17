"""CLI entry point for monthly FIDE progression automation."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from .article import write_article
from .config_loader import load_config
from .fide_etl import (
    bootstrap_database,
    create_sqlite_db,
    download_and_load,
    end_month_to_fide_token,
    load_file,
)
from .performance import (
    calculate_monthly_improvements,
    detect_new_fide_players,
    load_fide_frame,
    report_month_to_period,
)
from .roster import (
    export_roster_from_sqlite,
    refresh_roster_from_mdb,
)


def _default_report_month() -> str:
    today = date.today()
    first_of_month = today.replace(day=1)
    previous = first_of_month - timedelta(days=1)
    return previous.strftime("%Y-%m")


def _default_publish_date() -> str:
    return date.today().isoformat()


def cmd_generate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    period = report_month_to_period(args.report_month)
    db_path = Path(args.db or config["db_path"])
    roster_path = Path(args.roster or config["roster_path"])
    output_dir = Path(args.output)
    top_n = args.top or config["top_n"]

    if not db_path.exists():
        print(f"FIDE database not found: {db_path}", file=sys.stderr)
        return 1

    from .roster import load_roster

    roster = load_roster(roster_path)
    create_sqlite_db(db_path)

    with sqlite3.connect(db_path) as conn:
        frame = load_fide_frame(conn, config["federations"])

    performers = calculate_monthly_improvements(
        frame,
        roster,
        period.start_month,
        period.end_month,
    )
    new_players = detect_new_fide_players(
        frame,
        roster,
        period.start_month,
        period.end_month,
    )

    destination = write_article(
        output_dir,
        period,
        args.publish_date,
        performers,
        new_players,
        top_n,
        force=args.force,
    )
    if destination is None:
        return 0

    print(
        f"Generated article for {period.month_name_fr} {period.year} "
        f"({period.start_month} → {period.end_month})"
    )
    return 0


def cmd_refresh_roster(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    club_ref = args.club_ref or config["club_ref"]
    output_path = Path(args.output or config["roster_path"])

    if args.from_sqlite:
        export_roster_from_sqlite(args.from_sqlite, club_ref, output_path)
        return 0

    if args.from_mdb:
        refresh_roster_from_mdb(args.from_mdb, club_ref, output_path)
        return 0

    print("Provide --from-sqlite or --from-mdb.", file=sys.stderr)
    return 1


def cmd_download(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db_path = Path(args.db or config["db_path"])

    if args.month:
        token = args.month
    elif args.report_month:
        period = report_month_to_period(args.report_month)
        token = period.fide_token
    else:
        period = report_month_to_period(_default_report_month())
        token = period.fide_token

    create_sqlite_db(db_path)
    success = download_and_load(
        token,
        database=db_path,
        max_retries=args.retries,
        retry_delay_seconds=args.retry_delay,
    )
    return 0 if success else 1


def cmd_bootstrap(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db_path = Path(args.db or config["db_path"])
    bootstrap_database(months=args.months, database=db_path)
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db_path = Path(args.db or config["db_path"])
    create_sqlite_db(db_path)
    load_file(args.file, database=db_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JEEN monthly FIDE progression tooling")
    parser.add_argument("--config", help="Path to config.yaml")

    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a Pelican progression article")
    generate.add_argument(
        "--report-month",
        default=_default_report_month(),
        help="Report month in YYYY-MM format (default: previous calendar month)",
    )
    generate.add_argument(
        "--publish-date",
        default=_default_publish_date(),
        help="Article publish date YYYY-MM-DD (default: today)",
    )
    generate.add_argument("--top", type=int, help="Number of top performers (default from config)")
    generate.add_argument(
        "--output",
        default="content/articles",
        help="Output directory for generated articles",
    )
    generate.add_argument("--db", help="Path to fide_ratings.db")
    generate.add_argument("--roster", help="Path to jeen_roster.csv")
    generate.add_argument("--force", action="store_true", help="Overwrite an existing article")
    generate.set_defaults(func=cmd_generate)

    refresh = subparsers.add_parser("refresh-roster", help="Refresh committed club roster CSV")
    refresh.add_argument("--from-sqlite", help="Path to FFE Data.sqlite")
    refresh.add_argument("--from-mdb", help="Path to FFE Data.mdb (requires mdbtools)")
    refresh.add_argument("--club-ref", type=int, help="FFE club reference (default from config)")
    refresh.add_argument("--output", help="Output CSV path")
    refresh.set_defaults(func=cmd_refresh_roster)

    download = subparsers.add_parser("download", help="Download and load a FIDE monthly file")
    download.add_argument("--month", help="FIDE token such as mar26")
    download.add_argument("--report-month", help="Derive FIDE token from report month YYYY-MM")
    download.add_argument("--db", help="Path to fide_ratings.db")
    download.add_argument("--retries", type=int, default=1, help="Download retry attempts")
    download.add_argument(
        "--retry-delay",
        type=int,
        default=3600,
        help="Delay in seconds between download retries",
    )
    download.set_defaults(func=cmd_download)

    bootstrap = subparsers.add_parser(
        "bootstrap",
        help="Download recent FIDE months to seed the local database cache",
    )
    bootstrap.add_argument("--months", type=int, default=12, help="Number of months to download")
    bootstrap.add_argument("--db", help="Path to fide_ratings.db")
    bootstrap.set_defaults(func=cmd_bootstrap)

    load_cmd = subparsers.add_parser("load", help="Load a local FIDE text file into SQLite")
    load_cmd.add_argument("file", help="Path to standard_*frl.txt")
    load_cmd.add_argument("--db", help="Path to fide_ratings.db")
    load_cmd.set_defaults(func=cmd_load)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
