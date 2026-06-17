"""Pelican article generation for monthly progression reports."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .performance import ReportPeriod

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"


def article_filename(period: ReportPeriod, publish_date: str) -> str:
    """Build the article filename following existing site conventions."""
    return f"{publish_date} Progression {period.month_slug} {period.year}.md"


def article_path(output_dir: Path | str, period: ReportPeriod, publish_date: str) -> Path:
    """Return the full output path for a generated article."""
    return Path(output_dir) / article_filename(period, publish_date)


def format_performer_row(name: str, old_rating: int, new_rating: int, progression: int) -> str:
    """Format one markdown table row matching published articles."""
    return (
        f"| {name:<25} | {old_rating:<15} | {new_rating:<11} | {progression:<11} |"
    )


def render_article(
    period: ReportPeriod,
    publish_date: str,
    performers: list[dict],
    new_players: list[dict],
    top_n: int,
) -> str:
    """Render a Pelican article from the progression template."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("progression.md.j2")

    performer_rows = [
        format_performer_row(
            row["name"],
            row["old_rating"],
            row["new_rating"],
            row["progression"],
        )
        for row in performers[:top_n]
    ]

    return template.render(
        month_name_fr=period.month_name_fr,
        year=period.year,
        publish_date=publish_date,
        top_n=top_n,
        performer_rows=performer_rows,
        new_players=new_players,
    )


def write_article(
    output_dir: Path | str,
    period: ReportPeriod,
    publish_date: str,
    performers: list[dict],
    new_players: list[dict],
    top_n: int,
    force: bool = False,
) -> Path | None:
    """
    Write the article file if it does not already exist.

    Returns the written path, or None when skipped for idempotency.
    """
    destination = article_path(output_dir, period, publish_date)
    if destination.exists() and not force:
        print(f"Article already exists: {destination}. Skipping.")
        return None

    destination.parent.mkdir(parents=True, exist_ok=True)
    content = render_article(period, publish_date, performers, new_players, top_n)
    destination.write_text(content, encoding="utf-8")
    print(f"Wrote article: {destination}")
    return destination
