from pathlib import Path
import sqlite3
import pandas as pd

QUERIES={
"state_summary": """SELECT h.state, r.measure_id, COUNT(*) observations, SUM(r.score IS NOT NULL) available_scores, ROUND(100.0*SUM(r.score IS NOT NULL)/COUNT(*),1) completeness_pct, ROUND(AVG(r.score),2) avg_readmission_score, ROUND(SUM(r.score*r.denominator)/NULLIF(SUM(r.denominator),0),2) denominator_weighted_score, ROUND(SUM(r.denominator),0) total_denominator FROM fact_readmission r JOIN dim_hospital h USING(facility_id) GROUP BY h.state,r.measure_id""",
"hospital_opportunity": """SELECT h.facility_id,h.facility_name,h.state,h.county,r.measure_id,r.score,r.denominator,r.number_of_patients,r.number_returned,r.compared_to_national,r.footnote,h.overall_rating FROM fact_readmission r JOIN dim_hospital h USING(facility_id) ORDER BY r.score IS NULL,r.score DESC""",
"county_risk": """SELECT c.year,c.state,c.county,c.county_fips,c.measure_id,c.measure_name,c.data_value,c.low_ci,c.high_ci,c.population,c.value_type,COUNT(DISTINCT h.facility_id) hospital_count FROM fact_county_health c LEFT JOIN dim_hospital h ON c.county_key=h.county_key AND NOT EXISTS (SELECT 1 FROM qa_ambiguous_county_keys a WHERE a.county_key=c.county_key AND a.year=c.year AND a.measure_id=c.measure_id) GROUP BY c.year,c.county_fips,c.measure_id""",
"joined_model": """SELECT * FROM vw_hospital_readmission_county""",
"data_quality": """SELECT 'hospital_count' metric,COUNT(*) value FROM dim_hospital UNION ALL SELECT 'readmission_rows',COUNT(*) FROM fact_readmission UNION ALL SELECT 'readmission_scores_available',SUM(score IS NOT NULL) FROM fact_readmission UNION ALL SELECT 'unmatched_hospitals',COUNT(*) FROM qa_unmatched_hospitals UNION ALL SELECT 'ambiguous_county_keys',COUNT(DISTINCT county_key) FROM qa_ambiguous_county_keys"""
}

def export_all(db_path,out_dir):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); con=sqlite3.connect(db_path); counts={}
    for name,sql in QUERIES.items():
        df=pd.read_sql_query(sql,con); df.to_csv(out/f"{name}.csv",index=False); counts[name]=len(df)
    for table in ["dim_hospital","fact_readmission","fact_hcahps","fact_county_health","source_snapshot","qa_unmatched_hospitals","qa_ambiguous_county_keys"]:
        df=pd.read_sql_query(f"SELECT * FROM {table}",con); df.to_csv(out/f"{table}.csv",index=False); counts[table]=len(df)
    con.close(); return counts
