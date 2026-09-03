import sqlite3
import pandas as pd

from healthcare_intelligence.clean import (
    normalize_county_key,
    parse_numeric,
    clean_hospitals,
    clean_readmissions,
    clean_places,
)
from healthcare_intelligence.warehouse import build_warehouse


def test_parse_numeric_handles_cms_sentinels():
    assert parse_numeric("12.4") == 12.4
    assert pd.isna(parse_numeric("Not Available"))
    assert pd.isna(parse_numeric(""))


def test_normalize_county_key_removes_suffix_and_punctuation():
    assert normalize_county_key("St. Louis County", "MO") == "MO|ST LOUIS"
    assert normalize_county_key("LaSalle Parish", "LA") == "LA|LASALLE"


def test_clean_hospitals_preserves_six_character_facility_id():
    raw = pd.DataFrame([{"Facility ID": "01234", "Facility Name": "A", "State": "TX", "County/Parish": "Travis"}])
    out = clean_hospitals(raw)
    assert out.iloc[0]["facility_id"] == "001234"


def test_clean_readmissions_filters_required_measures_and_keeps_unavailable():
    raw = pd.DataFrame([
        {"Facility ID":"1", "Measure ID":"READM_30_HF", "Score":"20.1", "Denominator":"250", "Footnote":""},
        {"Facility ID":"1", "Measure ID":"OTHER", "Score":"3", "Denominator":"10", "Footnote":""},
        {"Facility ID":"2", "Measure ID":"READM_30_COPD", "Score":"Not Available", "Denominator":"Not Available", "Footnote":"sample too small"},
    ])
    out = clean_readmissions(raw)
    assert out["measure_id"].tolist() == ["READM_30_HF", "READM_30_COPD"]
    assert out["score"].notna().sum() == 1
    assert out.iloc[0]["denominator"] == 250
    assert len(out) == 2


def test_clean_places_prefers_age_adjusted_and_builds_county_key():
    raw = pd.DataFrame([
        {"year":"2023","stateabbr":"TX","locationname":"Travis","locationid":"48453","measureid":"DIABETES","datavaluetypeid":"CrdPrv","data_value":"11"},
        {"year":"2023","stateabbr":"TX","locationname":"Travis","locationid":"48453","measureid":"DIABETES","datavaluetypeid":"AgeAdjPrv","data_value":"9.5"},
    ])
    out = clean_places(raw)
    assert len(out) == 1
    assert out.iloc[0]["data_value"] == 9.5
    assert out.iloc[0]["county_key"] == "TX|TRAVIS"
    assert out.iloc[0]["value_type"] == "AgeAdjPrv"


def test_warehouse_retains_unmatched_hospitals(tmp_path):
    hospitals = pd.DataFrame([{"facility_id":"1","facility_name":"A","state":"TX","county":"Travis","county_key":"TX|TRAVIS"}, {"facility_id":"2","facility_name":"B","state":"TX","county":"Missing","county_key":"TX|MISSING"}])
    readm = pd.DataFrame([{"facility_id":"1","measure_id":"READM_30_HF","measure_name":"HF","score":20.0,"compared_to_national":"Same","footnote":None,"start_date":None,"end_date":None}])
    hcahps = pd.DataFrame(columns=["facility_id","measure_id","measure_name","score","response_rate","start_date","end_date"])
    places = pd.DataFrame([{"year":2023,"state":"TX","county":"Travis","county_fips":"48453","county_key":"TX|TRAVIS","measure_id":"DIABETES","measure_name":"Diabetes","value_type":"AgeAdjPrv","data_value":9.5,"low_ci":9.0,"high_ci":10.0,"population":100}])
    db = tmp_path / "x.db"
    build_warehouse(db, hospitals, readm, hcahps, places, pd.DataFrame())
    con = sqlite3.connect(db)
    assert con.execute("select count(*) from dim_hospital").fetchone()[0] == 2
    assert con.execute("select count(*) from qa_unmatched_hospitals").fetchone()[0] == 1


def test_warehouse_excludes_ambiguous_normalized_county_keys_from_join(tmp_path):
    hospitals = pd.DataFrame([
        {"facility_id": "1", "facility_name": "A", "state": "MD", "county": "Baltimore", "county_key": "MD|BALTIMORE"}
    ])
    readm = pd.DataFrame([
        {"facility_id": "1", "measure_id": "READM_30_HF", "measure_name": "HF", "score": 20.0, "compared_to_national": "Same", "footnote": None, "start_date": None, "end_date": None}
    ])
    hcahps = pd.DataFrame(columns=["facility_id", "measure_id", "measure_name", "score", "response_rate", "start_date", "end_date"])
    places = pd.DataFrame([
        {"year": 2023, "state": "MD", "county": "Baltimore", "county_fips": "24005", "county_key": "MD|BALTIMORE", "measure_id": "DIABETES", "measure_name": "Diabetes", "value_type": "AgeAdjPrv", "data_value": 10.0, "low_ci": 9.0, "high_ci": 11.0, "population": 850000},
        {"year": 2023, "state": "MD", "county": "Baltimore city", "county_fips": "24510", "county_key": "MD|BALTIMORE", "measure_id": "DIABETES", "measure_name": "Diabetes", "value_type": "AgeAdjPrv", "data_value": 12.0, "low_ci": 11.0, "high_ci": 13.0, "population": 570000},
    ])
    db = tmp_path / "ambiguous.db"

    build_warehouse(db, hospitals, readm, hcahps, places, pd.DataFrame())

    con = sqlite3.connect(db)
    assert con.execute("select count(*) from qa_ambiguous_county_keys").fetchone()[0] == 1
    joined = con.execute("select count(*), count(risk_measure_id) from vw_hospital_readmission_county").fetchone()
    assert joined == (1, 0)
    con.close()


def test_powerbi_survey_measures_aggregate_at_hospital_grain():
    dax = (__import__("pathlib").Path(__file__).parents[1] / "powerbi" / "measures.dax").read_text(encoding="utf-8")
    compact = " ".join(dax.split())
    assert "SUMX( VALUES(dim_hospital[facility_id])" in compact
    assert "MAX(fact_hcahps[completed_surveys])" in compact
    assert "HASONEVALUE(fact_readmission[measure_id])" in compact


def test_pbip_contains_no_personal_absolute_paths():
    root = __import__("pathlib").Path(__file__).parents[1]
    pbip = root / "powerbi" / "pbip"
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in pbip.rglob("*")
        if path.is_file()
    ).lower()
    assert "c:/users/" not in text
    assert "c:\\users\\" not in text
    assert "sai pavan" not in text


def test_pbip_source_snapshot_maps_exported_manifest_columns():
    root = __import__("pathlib").Path(__file__).parents[1]
    tmdl = (
        root
        / "powerbi"
        / "pbip"
        / "Healthcare Readmission Intelligence.SemanticModel"
        / "definition"
        / "tables"
        / "Source_Snapshot.tmdl"
    ).read_text(encoding="utf-8")
    assert 'Table.RenameColumns(Promoted,{{"source_name", "dataset"}' in tmdl
    assert '{"retrieved_at_utc", "retrieved_at"}' in tmdl
    assert '{"rows", "row_count"}' in tmdl


def test_pbip_percent_measures_convert_percentage_points_to_ratios():
    root = __import__("pathlib").Path(__file__).parents[1]
    metrics = (
        root
        / "powerbi"
        / "pbip"
        / "Healthcare Readmission Intelligence.SemanticModel"
        / "definition"
        / "tables"
        / "Metrics.tmdl"
    ).read_text(encoding="utf-8")
    assert metrics.count(", 100)") >= 2
    assert metrics.count("formatString: 0.0%") >= 2


def test_data_quality_counts_distinct_ambiguous_county_keys():
    from healthcare_intelligence.analytics import QUERIES

    compact = " ".join(QUERIES["data_quality"].lower().split())
    assert "count(distinct county_key) from qa_ambiguous_county_keys" in compact
