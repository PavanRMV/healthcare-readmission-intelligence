# Data dictionary

| Table | Grain | Key fields | Analytical fields |
|---|---|---|---|
| dim_hospital | one hospital | facility_id (TEXT, 6 chars), county_key | name, geography, type, ownership, overall_rating |
| fact_readmission | hospital × CMS measure | facility_id, measure_id | score, denominator, number_of_patients, number_returned, comparison, footnote, period |
| fact_hcahps | hospital × HCAHPS answer | facility_id, measure_id, answer_description | star score, answer percent, completed surveys, response rate, footnote, period |
| fact_county_health | county × year × measure | county_fips, measure_id, year | modeled estimate, value_type, confidence limits, population, county_key |
| source_snapshot | one source per run | dataset_id | resolved URL, retrieval time, release/modified, SHA-256, bytes, raw rows |
| qa_unmatched_hospitals | one unmatched hospital | facility_id | original/normalized county fields and reason |
| qa_ambiguous_county_keys | normalized key × year × measure | county_key, year, measure_id | distinct FIPS count/list and source row count |

`score` is the source-provided CMS value and is not recomputed. NULL means unavailable/invalid source text—not zero. `modeled_county_estimate` is a CDC PLACES modeled prevalence percentage. HCAHPS `completed_surveys` and `response_rate` repeat across measure rows for a hospital; aggregate once per facility (for example, `MAX` per facility followed by `SUM`/`AVERAGE`), never with a raw fact-table sum.
