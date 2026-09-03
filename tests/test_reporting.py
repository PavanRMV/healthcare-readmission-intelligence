import sqlite3

import pandas as pd

from healthcare_intelligence.reporting import (
    _opportunity_chart_data,
    _overview_cards,
    build_kpis,
    generate_report,
)


def _sample_db(path):
    con = sqlite3.connect(path)
    pd.DataFrame(
        [
            {"facility_id": "000001", "facility_name": "Alpha", "state": "TX", "county": "Travis", "county_key": "TX|TRAVIS", "overall_rating": 4.0},
            {"facility_id": "000002", "facility_name": "Beta", "state": "CA", "county": "Orange", "county_key": "CA|ORANGE", "overall_rating": 2.0},
        ]
    ).to_sql("dim_hospital", con, index=False)
    pd.DataFrame(
        [
            {"facility_id": "000001", "measure_id": "READM_30_HF", "score": 20.0, "denominator": 100.0},
            {"facility_id": "000002", "measure_id": "READM_30_HF", "score": None, "denominator": None},
            {"facility_id": "000001", "measure_id": "READM_30_PN", "score": 10.0, "denominator": 300.0},
        ]
    ).to_sql("fact_readmission", con, index=False)
    pd.DataFrame(
        [{"facility_id": "000001", "measure_id": "H_STAR", "score": 4.0, "completed_surveys": 120.0, "response_rate": 35.0}]
    ).to_sql("fact_hcahps", con, index=False)
    pd.DataFrame(
        [{"year": 2023, "state": "TX", "county": "Travis", "county_key": "TX|TRAVIS", "measure_id": "DIABETES", "data_value": 10.0, "population": 1000.0}]
    ).to_sql("fact_county_health", con, index=False)
    pd.DataFrame([{"facility_id": "000002"}]).to_sql("qa_unmatched_hospitals", con, index=False)
    pd.DataFrame(columns=["county_key", "year", "measure_id"]).to_sql("qa_ambiguous_county_keys", con, index=False)
    con.close()


def test_build_kpis_is_denominator_aware_and_reports_coverage(tmp_path):
    db = tmp_path / "sample.db"
    _sample_db(db)

    kpis = build_kpis(db)

    assert kpis["hospital_count"] == 2
    assert kpis["readmission_rows"] == 3
    assert kpis["readmission_available"] == 2
    assert kpis["readmission_completeness_pct"] == 66.7
    assert kpis["total_readmission_denominator"] == 400
    assert "weighted_readmission_score" not in kpis
    assert kpis["county_join_coverage_pct"] == 50.0
    assert kpis["ambiguous_county_hospitals"] == 0
    assert kpis["places_latest_year"] == 2023


def test_build_kpis_excludes_ambiguous_hospitals_from_safe_coverage(tmp_path):
    db = tmp_path / "sample.db"
    _sample_db(db)
    with sqlite3.connect(db) as con:
        con.execute("INSERT INTO qa_ambiguous_county_keys VALUES ('TX|TRAVIS', 2023, 'DIABETES')")

    kpis = build_kpis(db)

    assert kpis["ambiguous_county_hospitals"] == 1
    assert kpis["county_join_coverage_pct"] == 0.0


def test_generate_report_writes_two_pngs_and_machine_readable_summary(tmp_path):
    db = tmp_path / "sample.db"
    output_dir = tmp_path / "report"
    _sample_db(db)

    manifest = generate_report(db, output_dir)

    assert manifest["files"] == [
        "executive_overview.png",
        "hospital_opportunity.png",
        "executive_summary.md",
        "kpis.json",
    ]
    for name in manifest["files"]:
        assert (output_dir / name).stat().st_size > 100
    assert (output_dir / "executive_overview.png").read_bytes().startswith(b"\x89PNG")
    summary = (output_dir / "executive_summary.md").read_text(encoding="utf-8")
    assert "Executive summary" in summary
    assert "66.7%" in summary
    assert "descriptive" in summary.lower()


def test_overview_cards_use_non_composite_volume_kpi():
    cards = _overview_cards(
        {
            "hospital_count": 2,
            "readmission_available": 2,
            "readmission_completeness_pct": 66.7,
            "county_join_coverage_pct": 50.0,
        }
    )

    assert ("AVAILABLE SCORES", "2") in cards
    assert all(label != "WEIGHTED SCORE" for label, _ in cards)


def test_opportunity_chart_data_sorts_gaps_and_makes_labels_unique():
    rows = pd.DataFrame(
        [
            {"facility_name": "A Very Long Hospital Name That Needs Truncation", "state": "TX", "measure_id": "READM_30_HF", "gap_to_state": 8.0},
            {"facility_name": "Beta", "state": "CA", "measure_id": "READM_30_PN", "gap_to_state": 3.0},
            {"facility_name": "Beta", "state": "CA", "measure_id": "READM_30_HF", "gap_to_state": 5.0},
        ]
    )

    chart = _opportunity_chart_data(rows)

    assert chart["gap_to_state"].tolist() == [3.0, 5.0, 8.0]
    assert chart["label"].is_unique
    assert chart.iloc[0]["label"].endswith("PN · CA")
    assert max(chart["label"].str.len()) <= 36
