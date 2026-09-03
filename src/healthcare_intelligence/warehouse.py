from pathlib import Path
import sqlite3

def build_warehouse(path,hospitals,readmissions,hcahps,places,snapshots):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): path.unlink()
    con=sqlite3.connect(path)
    hospitals.to_sql("dim_hospital",con,index=False)
    readmissions.to_sql("fact_readmission",con,index=False)
    hcahps.to_sql("fact_hcahps",con,index=False)
    places.to_sql("fact_county_health",con,index=False)
    if snapshots.empty and len(snapshots.columns) == 0:
        snapshots = __import__("pandas").DataFrame(columns=["source_name","dataset_id","source_url","retrieved_at_utc","source_modified","source_released","sha256","bytes","rows"])
    snapshots.to_sql("source_snapshot",con,index=False)
    for name in ["denominator","number_of_patients","number_returned"]:
        if name not in readmissions.columns:
            con.execute(f"ALTER TABLE fact_readmission ADD COLUMN {name} REAL")
    unmatched=hospitals.loc[~hospitals.county_key.isin(set(places.county_key.dropna()))].copy()
    unmatched["qa_reason"]="No normalized state/county key match to CDC PLACES"
    unmatched.to_sql("qa_unmatched_hospitals",con,index=False)
    con.executescript("""
    CREATE TABLE qa_ambiguous_county_keys AS
    SELECT county_key, year, measure_id,
           COUNT(DISTINCT county_fips) AS county_fips_count,
           GROUP_CONCAT(DISTINCT county_fips) AS county_fips_values,
           COUNT(*) AS source_rows
    FROM fact_county_health
    WHERE county_key IS NOT NULL
    GROUP BY county_key, year, measure_id
    HAVING COUNT(DISTINCT county_fips) > 1;

    CREATE UNIQUE INDEX ix_hospital_id ON dim_hospital(facility_id);
    CREATE INDEX ix_hospital_county ON dim_hospital(county_key);
    CREATE INDEX ix_readm_facility ON fact_readmission(facility_id);
    CREATE INDEX ix_places_county ON fact_county_health(county_key);
    CREATE VIEW vw_hospital_readmission_county AS
    SELECT h.facility_id,h.facility_name,h.state,h.county,h.county_key,r.measure_id,r.measure_name,r.score,r.denominator,r.number_of_patients,r.number_returned,r.compared_to_national,r.footnote,r.start_date,r.end_date,
           c.measure_id AS risk_measure_id,c.measure_name AS risk_measure_name,c.data_value AS modeled_county_estimate,c.low_ci,c.high_ci,c.population,c.value_type,c.year AS places_year
    FROM dim_hospital h LEFT JOIN fact_readmission r ON h.facility_id=r.facility_id
    LEFT JOIN fact_county_health c
      ON h.county_key=c.county_key
     AND NOT EXISTS (
       SELECT 1 FROM qa_ambiguous_county_keys a
       WHERE a.county_key=c.county_key
         AND a.year=c.year
         AND a.measure_id=c.measure_id
     );
    """)
    con.commit(); con.close()
