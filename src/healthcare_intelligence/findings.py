import json, sqlite3
from pathlib import Path
import pandas as pd
from .reporting import build_kpis

def generate(db_path, markdown_path, json_path):
    con=sqlite3.connect(db_path)
    overall=pd.read_sql_query("""SELECT measure_id,COUNT(*) rows,SUM(score IS NOT NULL) available,ROUND(100.0*SUM(score IS NOT NULL)/COUNT(*),1) completeness_pct,ROUND(AVG(score),2) mean_score,ROUND(SUM(score*denominator)/NULLIF(SUM(denominator),0),2) weighted_score,CAST(SUM(denominator) AS INTEGER) total_denominator FROM fact_readmission GROUP BY measure_id ORDER BY measure_id""",con)
    states=pd.read_sql_query("""SELECT h.state,r.measure_id,COUNT(r.score) available,ROUND(AVG(r.score),2) mean_score,CAST(SUM(r.denominator) AS INTEGER) denominator FROM fact_readmission r JOIN dim_hospital h USING(facility_id) WHERE r.score IS NOT NULL GROUP BY h.state,r.measure_id HAVING COUNT(r.score)>=20 AND SUM(r.denominator)>=1000 ORDER BY mean_score DESC LIMIT 5""",con)
    county=pd.read_sql_query("""SELECT measure_id,state,county,data_value,low_ci,high_ci,population,value_type FROM fact_county_health WHERE data_value IS NOT NULL AND population>=10000 ORDER BY data_value DESC LIMIT 7""",con)
    hc=pd.read_sql_query("""SELECT COUNT(*) rows,SUM(score IS NOT NULL) star_available,SUM(completed_surveys IS NOT NULL) sample_available,SUM(response_rate IS NOT NULL) response_available FROM fact_hcahps""",con).iloc[0].to_dict()
    unmatched=con.execute("SELECT COUNT(*) FROM qa_unmatched_hospitals").fetchone()[0]; hospitals=con.execute("SELECT COUNT(*) FROM dim_hospital").fetchone()[0]
    latest=con.execute("SELECT MAX(year) FROM fact_county_health").fetchone()[0]; con.close()
    quality=build_kpis(db_path)
    payload={"readmission_by_measure":overall.to_dict("records"),"high_state_measure_descriptive":states.to_dict("records"),"highest_modeled_county_estimates_population_ge_10000":county.to_dict("records"),"hcahps_completeness":hc,"hospital_count":hospitals,"unmatched_hospitals":unmatched,"ambiguous_county_hospitals":quality["ambiguous_county_hospitals"],"safe_joined_hospitals":quality["safe_county_matched_hospitals"],"join_coverage_pct":quality["county_join_coverage_pct"],"places_latest_year":int(latest)}
    Path(json_path).write_text(json.dumps(payload,indent=2),encoding="utf-8")
    lines=["# Executed findings", "", "Generated from the live-run SQLite warehouse. This is a **current CMS extract**, not a historical trend. CDC PLACES values are **modeled county estimates**. Findings are descriptive and do not establish causality.", "", "## Readmission measures", "", "| Measure | Rows | Available | Completeness | Mean score | Denominator-weighted score | Total denominator |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in payload["readmission_by_measure"]: lines.append(f'| {r["measure_id"]} | {r["rows"]} | {r["available"]} | {r["completeness_pct"]}% | {r["mean_score"]} | {r["weighted_score"]} | {r["total_denominator"] or "n/a"} |')
    lines += ["", f'Safe county join coverage was **{payload["join_coverage_pct"]}%** ({payload["safe_joined_hospitals"]:,}/{hospitals:,} hospitals); **{unmatched:,}** unmatched and **{payload["ambiguous_county_hospitals"]:,}** hospitals on ambiguous normalized keys remain visible in QA outputs.', "", "## Descriptive high state/measure averages", "", "Restricted to cells with at least 20 available scores and total denominator ≥1,000. These are comparison prompts, not performance verdicts; case mix and measure specifications matter.", "", "| State | Measure | Available | Mean | Denominator |", "|---|---|---:|---:|---:|"]
    for r in payload["high_state_measure_descriptive"]: lines.append(f'| {r["state"]} | {r["measure_id"]} | {r["available"]} | {r["mean_score"]} | {r["denominator"]} |')
    lines += ["", "## Community context", "", f'The latest PLACES year in this run is **{latest}**. The highest modeled estimates below are limited to counties with population ≥10,000 and must not be interpreted as hospital patient prevalence or causes of readmission.', "", "| Measure | County | Modeled estimate | 95% interval | Population | Type |", "|---|---|---:|---:|---:|---|"]
    for r in payload["highest_modeled_county_estimates_population_ge_10000"]: lines.append(f'| {r["measure_id"]} | {r["county"]}, {r["state"]} | {r["data_value"]} | {r["low_ci"]}–{r["high_ci"]} | {int(r["population"])} | {r["value_type"]} |')
    lines += ["", "## HCAHPS availability", "", f'HCAHPS contains {int(hc["rows"]):,} rows; star values are present on {int(hc["star_available"]):,}, completed-survey values on {int(hc["sample_available"]):,}, and response-rate values on {int(hc["response_available"]):,}. Use these fields and footnotes when comparing hospitals.', ""]
    Path(markdown_path).write_text("\n".join(lines),encoding="utf-8")
    return payload
