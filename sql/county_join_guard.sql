-- Idempotent guard for normalized county-key collisions.
-- Distinct county FIPS that collapse to one county_key are excluded from the
-- hospital/county view at year/measure grain and remain visible in QA.
DROP VIEW IF EXISTS vw_hospital_readmission_county;
DROP TABLE IF EXISTS qa_ambiguous_county_keys;

CREATE TABLE qa_ambiguous_county_keys AS
SELECT county_key, year, measure_id,
       COUNT(DISTINCT county_fips) AS county_fips_count,
       GROUP_CONCAT(DISTINCT county_fips) AS county_fips_values,
       COUNT(*) AS source_rows
FROM fact_county_health
WHERE county_key IS NOT NULL
GROUP BY county_key, year, measure_id
HAVING COUNT(DISTINCT county_fips) > 1;

CREATE VIEW vw_hospital_readmission_county AS
SELECT h.facility_id, h.facility_name, h.state, h.county, h.county_key,
       r.measure_id, r.measure_name, r.score, r.denominator,
       r.number_of_patients, r.number_returned, r.compared_to_national,
       r.footnote, r.start_date, r.end_date,
       c.measure_id AS risk_measure_id,
       c.measure_name AS risk_measure_name,
       c.data_value AS modeled_county_estimate,
       c.low_ci, c.high_ci, c.population, c.value_type,
       c.year AS places_year
FROM dim_hospital AS h
LEFT JOIN fact_readmission AS r ON r.facility_id = h.facility_id
LEFT JOIN fact_county_health AS c
  ON c.county_key = h.county_key
 AND NOT EXISTS (
     SELECT 1
     FROM qa_ambiguous_county_keys AS a
     WHERE a.county_key = c.county_key
       AND a.year = c.year
       AND a.measure_id = c.measure_id
 );
