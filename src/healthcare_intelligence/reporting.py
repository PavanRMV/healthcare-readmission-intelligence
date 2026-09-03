"""Portfolio reporting and static dashboard generation from the SQLite warehouse."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def build_kpis(db_path: str | Path) -> dict[str, int | float | None]:
    """Return headline metrics without loading fact tables into memory."""
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            """
            SELECT COUNT(*) AS row_count,
                   SUM(score IS NOT NULL) AS available_count,
                   SUM(CASE WHEN score IS NOT NULL THEN denominator END) AS total_denominator
            FROM fact_readmission
            """
        ).fetchone()
        hospitals = con.execute("SELECT COUNT(*) FROM dim_hospital").fetchone()[0]
        unmatched = con.execute("SELECT COUNT(*) FROM qa_unmatched_hospitals").fetchone()[0]
        ambiguous = con.execute(
            """
            SELECT COUNT(DISTINCT h.facility_id)
            FROM dim_hospital h
            JOIN qa_ambiguous_county_keys a ON a.county_key = h.county_key
            """
        ).fetchone()[0]
        safe_matches = con.execute(
            """
            SELECT COUNT(*)
            FROM dim_hospital h
            WHERE NOT EXISTS (
                SELECT 1 FROM qa_unmatched_hospitals u WHERE u.facility_id = h.facility_id
            )
              AND NOT EXISTS (
                SELECT 1 FROM qa_ambiguous_county_keys a WHERE a.county_key = h.county_key
            )
            """
        ).fetchone()[0]
        latest_year = con.execute("SELECT MAX(year) FROM fact_county_health").fetchone()[0]

    readmission_rows, available, total_denominator = row
    completeness = 100.0 * available / readmission_rows if readmission_rows else None
    coverage = 100.0 * safe_matches / hospitals if hospitals else None
    return {
        "hospital_count": hospitals,
        "readmission_rows": readmission_rows,
        "readmission_available": available,
        "readmission_completeness_pct": round(completeness, 1) if completeness is not None else None,
        "total_readmission_denominator": int(total_denominator) if total_denominator is not None else 0,
        "unmatched_county_hospitals": unmatched,
        "ambiguous_county_hospitals": ambiguous,
        "safe_county_matched_hospitals": safe_matches,
        "county_join_coverage_pct": round(coverage, 1) if coverage is not None else None,
        "places_latest_year": latest_year,
    }


NAVY = "#16324F"
TEAL = "#176B87"
AQUA = "#64CCC5"
AMBER = "#F4A261"
RED = "#C94C4C"
MUTED = "#667085"
BACKGROUND = "#F7F9FC"


def _style_figure(fig, title: str, subtitle: str) -> None:
    fig.patch.set_facecolor(BACKGROUND)
    fig.suptitle(title, x=0.06, y=0.975, ha="left", fontsize=22, fontweight="bold", color=NAVY)
    fig.text(0.06, 0.935, subtitle, ha="left", fontsize=10, color=MUTED)


def _style_axis(ax) -> None:
    ax.set_facecolor("white")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_axisbelow(True)


def _overview_cards(kpis: dict) -> list[tuple[str, str]]:
    return [
        ("HOSPITALS", f'{kpis["hospital_count"]:,}'),
        ("AVAILABLE SCORES", f'{kpis["readmission_available"]:,}'),
        ("SCORE COMPLETENESS", f'{kpis["readmission_completeness_pct"]:.1f}%'),
        ("COUNTY JOIN COVERAGE", f'{kpis["county_join_coverage_pct"]:.1f}%'),
    ]


def _opportunity_chart_data(rows: pd.DataFrame) -> pd.DataFrame:
    chart = rows.sort_values("gap_to_state", kind="stable").copy()
    short_measure = chart["measure_id"].str.replace("READM_30_", "", regex=False)
    max_name = 25
    names = chart["facility_name"].str.slice(0, max_name).str.rstrip()
    names = names.where(chart["facility_name"].str.len() <= max_name, names + "…")
    chart["label"] = names + " · " + short_measure + " · " + chart["state"]
    return chart


def _executive_overview(db_path: str | Path, output_path: Path, kpis: dict) -> None:
    with sqlite3.connect(db_path) as con:
        measures = pd.read_sql_query(
            """
            SELECT measure_id,
                   100.0 * SUM(score IS NOT NULL) / COUNT(*) AS completeness,
                   SUM(score * denominator) /
                     NULLIF(SUM(CASE WHEN score IS NOT NULL THEN denominator END), 0) AS weighted_score
            FROM fact_readmission
            GROUP BY measure_id
            ORDER BY weighted_score DESC
            """,
            con,
        )
        states = pd.read_sql_query(
            """
            SELECT h.state,
                   SUM(r.score * r.denominator) /
                     NULLIF(SUM(CASE WHEN r.score IS NOT NULL THEN r.denominator END), 0) AS weighted_score,
                   COUNT(r.score) AS available
            FROM fact_readmission r
            JOIN dim_hospital h ON h.facility_id = r.facility_id
            WHERE r.measure_id = 'READM_30_HF'
            GROUP BY h.state
            HAVING COUNT(r.score) > 0
            ORDER BY weighted_score DESC
            LIMIT 10
            """,
            con,
        ).sort_values("weighted_score")

    fig = plt.figure(figsize=(16, 9), dpi=120)
    _style_figure(fig, "Readmission Intelligence | Executive Overview", "Current CMS extract • scores are descriptive, denominator-aware comparisons • CDC PLACES is modeled context")
    grid = fig.add_gridspec(3, 4, height_ratios=[0.8, 2.2, 2.3], hspace=0.48, wspace=0.38, left=0.06, right=0.96, top=0.87, bottom=0.08)
    cards = _overview_cards(kpis)
    for i, (label, value) in enumerate(cards):
        ax = fig.add_subplot(grid[0, i])
        ax.set_facecolor("white")
        ax.text(0.06, 0.68, value, transform=ax.transAxes, fontsize=25, fontweight="bold", color=TEAL)
        ax.text(0.06, 0.24, label, transform=ax.transAxes, fontsize=9, color=MUTED, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_color("#E5E7EB")

    ax1 = fig.add_subplot(grid[1:, :2])
    _style_axis(ax1)
    labels = measures["measure_id"].str.replace("READM_30_", "", regex=False)
    ax1.barh(labels, measures["weighted_score"], color=TEAL, alpha=0.9)
    ax1.invert_yaxis()
    ax1.set_title("Denominator-weighted score by measure", loc="left", color=NAVY, fontweight="bold")
    ax1.set_xlabel("30-day readmission score", color=MUTED)
    for y, value in enumerate(measures["weighted_score"]):
        ax1.text(value + 0.15, y, f"{value:.1f}", va="center", color=NAVY, fontsize=9)

    ax2 = fig.add_subplot(grid[1, 2:])
    _style_axis(ax2)
    colors = [AQUA if value >= 60 else AMBER if value >= 40 else RED for value in measures["completeness"]]
    ax2.barh(labels, measures["completeness"], color=colors)
    ax2.invert_yaxis(); ax2.set_xlim(0, 100)
    ax2.set_title("Score availability by measure", loc="left", color=NAVY, fontweight="bold")
    ax2.set_xlabel("available rows (%)", color=MUTED)

    ax3 = fig.add_subplot(grid[2, 2:])
    _style_axis(ax3)
    ax3.barh(states["state"], states["weighted_score"], color=AQUA)
    ax3.set_title("Highest state-level heart failure scores", loc="left", color=NAVY, fontweight="bold")
    ax3.set_xlabel("READM_30_HF denominator-weighted score", color=MUTED)
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _hospital_opportunity(db_path: str | Path, output_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as con:
        opportunities = pd.read_sql_query(
            """
            WITH state_measure AS (
              SELECT h.state, r.measure_id, AVG(r.score) AS state_avg
              FROM fact_readmission r JOIN dim_hospital h ON h.facility_id = r.facility_id
              WHERE r.score IS NOT NULL
              GROUP BY h.state, r.measure_id
            )
            SELECT h.facility_name, h.state, r.measure_id, r.score, r.denominator,
                   r.score - s.state_avg AS gap_to_state
            FROM fact_readmission r
            JOIN dim_hospital h ON h.facility_id = r.facility_id
            JOIN state_measure s ON s.state = h.state AND s.measure_id = r.measure_id
            WHERE r.score IS NOT NULL
            ORDER BY gap_to_state DESC, r.denominator DESC
            LIMIT 12
            """,
            con,
        )
        experience = pd.read_sql_query(
            """
            SELECT h.facility_id, h.overall_rating,
                   r.score AS readmission_score,
                   r.denominator
            FROM dim_hospital h JOIN fact_readmission r ON r.facility_id = h.facility_id
            WHERE h.overall_rating IS NOT NULL
              AND r.score IS NOT NULL
              AND r.measure_id = 'READM_30_HF'
            """,
            con,
        )

    display = _opportunity_chart_data(opportunities)
    fig = plt.figure(figsize=(16, 9), dpi=120)
    _style_figure(fig, "Hospital Opportunity | Screening View", "Gap versus same-state measure average • prioritize review, not punitive ranking • inspect denominator and footnotes before action")
    grid = fig.add_gridspec(1, 2, wspace=0.32, left=0.17, right=0.96, top=0.86, bottom=0.1)
    ax1 = fig.add_subplot(grid[0, 0]); _style_axis(ax1)
    ax1.barh(display["label"], display["gap_to_state"], color=AMBER)
    ax1.set_title("Largest positive gaps to state benchmark", loc="left", color=NAVY, fontweight="bold")
    ax1.set_xlabel("score points above state/measure mean", color=MUTED)
    ax2 = fig.add_subplot(grid[0, 1]); _style_axis(ax2)
    if not experience.empty:
        size = experience["denominator"].fillna(0).clip(lower=1) ** 0.5 * 2
        ax2.scatter(experience["overall_rating"], experience["readmission_score"], s=size, color=TEAL, alpha=0.35, edgecolors="none")
    ax2.set_title("Hospital rating vs. heart failure readmission", loc="left", color=NAVY, fontweight="bold")
    ax2.set_xlabel("CMS overall rating", color=MUTED); ax2.set_ylabel("READM_30_HF score", color=MUTED)
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return opportunities


def generate_report(db_path: str | Path, output_dir: str | Path) -> dict:
    """Create portfolio-ready dashboard previews and an executive KPI summary."""
    db_path, output_dir = Path(db_path), Path(output_dir)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite warehouse not found: {db_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    kpis = build_kpis(db_path)
    _executive_overview(db_path, output_dir / "executive_overview.png", kpis)
    opportunities = _hospital_opportunity(db_path, output_dir / "hospital_opportunity.png")
    top = opportunities.iloc[0].to_dict() if not opportunities.empty else None
    kpis["top_opportunity"] = top
    (output_dir / "kpis.json").write_text(json.dumps(kpis, indent=2, default=str), encoding="utf-8")
    top_line = (
        f'Largest screening gap: **{top["facility_name"]} ({top["state"]})**, '
        f'{top["measure_id"]}, **{top["gap_to_state"]:.2f} points** above its state mean.'
        if top else "No scored hospital opportunities were available."
    )
    summary = f"""# Executive summary

- **{kpis['hospital_count']:,} hospitals** and **{kpis['readmission_rows']:,} readmission rows** are represented.
- **{kpis['readmission_available']:,} scores** are available (**{kpis['readmission_completeness_pct']:.1f}%** of readmission rows); missing values remain null rather than being treated as zero.
- Available scored rows represent a reported denominator of **{kpis['total_readmission_denominator']:,}** across condition measures (not unique patients).
- Safe county context joins cover **{kpis['county_join_coverage_pct']:.1f}%** of hospitals; **{kpis['ambiguous_county_hospitals']:,}** hospitals on ambiguous normalized keys and **{kpis['unmatched_county_hospitals']:,}** unmatched hospitals are excluded. PLACES {kpis['places_latest_year']} values are modeled estimates.
- {top_line}

These are descriptive screening signals, not causal conclusions or quality verdicts. Review measure specifications, denominators, confidence intervals, and footnotes before decisions.
"""
    (output_dir / "executive_summary.md").write_text(summary, encoding="utf-8")
    return {"files": ["executive_overview.png", "hospital_opportunity.png", "executive_summary.md", "kpis.json"], "kpis": kpis}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PNG portfolio dashboards and KPI summary")
    parser.add_argument("--db", default="data/warehouse/healthcare.db")
    parser.add_argument("--output-dir", default="outputs/reporting")
    args = parser.parse_args()
    print(json.dumps(generate_report(args.db, args.output_dir), indent=2, default=str))


if __name__ == "__main__":
    main()
