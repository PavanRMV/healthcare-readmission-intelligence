-- Logical SQLite schema produced by the ETL. Types mirror pandas-to-SQL output.
CREATE TABLE dim_hospital (
  facility_id TEXT PRIMARY KEY, facility_name TEXT, address TEXT, city TEXT, state TEXT,
  zip_code TEXT, county TEXT, hospital_type TEXT, ownership TEXT, emergency_services TEXT,
  overall_rating REAL, readm_measure_count REAL, county_key TEXT
);
CREATE TABLE fact_readmission (
  facility_id TEXT NOT NULL, measure_id TEXT NOT NULL, measure_name TEXT, score REAL,
  denominator REAL, number_of_patients REAL, number_returned REAL,
  compared_to_national TEXT, footnote TEXT, start_date TEXT, end_date TEXT
);
CREATE TABLE fact_hcahps (
  facility_id TEXT NOT NULL, measure_id TEXT, measure_name TEXT, answer_description TEXT,
  score REAL, answer_percent REAL, completed_surveys REAL, response_rate REAL,
  footnote TEXT, start_date TEXT, end_date TEXT
);
CREATE TABLE fact_county_health (
  year INTEGER, state TEXT, county TEXT, county_fips TEXT, measure_id TEXT, measure_name TEXT,
  value_type TEXT, data_value REAL, low_ci REAL, high_ci REAL, population REAL, county_key TEXT
);
CREATE TABLE source_snapshot (
  source_name TEXT, dataset_id TEXT, source_url TEXT, retrieved_at_utc TEXT,
  source_modified TEXT, source_released TEXT, sha256 TEXT, bytes INTEGER, rows INTEGER
);
CREATE TABLE qa_unmatched_hospitals AS SELECT *, '' AS qa_reason FROM dim_hospital WHERE 0;
CREATE TABLE qa_ambiguous_county_keys (
  county_key TEXT, year INTEGER, measure_id TEXT, county_fips_count INTEGER,
  county_fips_values TEXT, source_rows INTEGER
);
CREATE INDEX ix_hospital_county ON dim_hospital(county_key);
CREATE INDEX ix_readm_facility ON fact_readmission(facility_id);
CREATE INDEX ix_places_county ON fact_county_health(county_key);
