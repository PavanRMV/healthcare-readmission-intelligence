-- Portfolio analysis: five decision-oriented questions.
-- SQLite only: no vendor-specific QUALIFY, FILTER, percentile, or date syntax.
-- Scores are descriptive; a higher readmission score is not treated as causal evidence.

-- Q1. STATE BENCHMARKING
-- Which state/measure cells have the highest denominator-weighted readmission scores,
-- and is there enough data to support a responsible comparison?
SELECT
    h.state,
    r.measure_id,
    COUNT(*) AS expected_rows,
    COUNT(r.score) AS scored_rows,
    ROUND(100.0 * COUNT(r.score) / COUNT(*), 1) AS completeness_pct,
    ROUND(AVG(r.score), 2) AS unweighted_score,
    ROUND(
        SUM(r.score * r.denominator) /
        NULLIF(SUM(CASE WHEN r.score IS NOT NULL THEN r.denominator END), 0),
        2
    ) AS denominator_weighted_score,
    CAST(SUM(CASE WHEN r.score IS NOT NULL THEN r.denominator END) AS INTEGER) AS denominator
FROM fact_readmission AS r
JOIN dim_hospital AS h ON h.facility_id = r.facility_id
GROUP BY h.state, r.measure_id
HAVING COUNT(r.score) >= 20
   AND SUM(CASE WHEN r.score IS NOT NULL THEN r.denominator END) >= 1000
ORDER BY denominator_weighted_score DESC, h.state, r.measure_id;

-- Q2. HOSPITAL OPPORTUNITY
-- Which scored hospitals sit furthest above their same-state, same-measure peer mean?
-- The denominator and CMS comparison label are retained to prevent score-only ranking.
WITH state_measure AS (
    SELECT h.state, r.measure_id, AVG(r.score) AS state_mean
    FROM fact_readmission AS r
    JOIN dim_hospital AS h ON h.facility_id = r.facility_id
    WHERE r.score IS NOT NULL
    GROUP BY h.state, r.measure_id
)
SELECT
    h.facility_id,
    h.facility_name,
    h.state,
    h.county,
    r.measure_id,
    ROUND(r.score, 2) AS hospital_score,
    ROUND(s.state_mean, 2) AS state_mean,
    ROUND(r.score - s.state_mean, 2) AS gap_to_state_mean,
    CAST(r.denominator AS INTEGER) AS denominator,
    r.compared_to_national,
    r.footnote,
    h.overall_rating
FROM fact_readmission AS r
JOIN dim_hospital AS h ON h.facility_id = r.facility_id
JOIN state_measure AS s
  ON s.state = h.state AND s.measure_id = r.measure_id
WHERE r.score IS NOT NULL
ORDER BY gap_to_state_mean DESC, r.denominator DESC
LIMIT 100;

-- Q3. PATIENT EXPERIENCE
-- How do HCAHPS star measures compare across states after enforcing a minimum
-- survey base? Completed surveys and response rates remain visible as context.
SELECT
    h.state,
    x.measure_id,
    x.measure_name,
    COUNT(x.score) AS hospitals_with_score,
    ROUND(AVG(x.score), 2) AS mean_star_rating,
    CAST(SUM(x.completed_surveys) AS INTEGER) AS completed_surveys,
    ROUND(AVG(x.response_rate), 1) AS mean_response_rate
FROM fact_hcahps AS x
JOIN dim_hospital AS h ON h.facility_id = x.facility_id
WHERE x.measure_id IN (
    'H_STAR_RATING',
    'H_HSP_RATING_STAR_RATING',
    'H_RECMND_STAR_RATING',
    'H_COMP_1_STAR_RATING',
    'H_COMP_2_STAR_RATING'
)
GROUP BY h.state, x.measure_id, x.measure_name
HAVING COUNT(x.score) >= 20
   AND SUM(x.completed_surveys) >= 1000
ORDER BY x.measure_id, mean_star_rating DESC, h.state;

-- Q4. DATA COMPLETENESS
-- Where are the largest score-availability gaps by readmission measure?
SELECT
    r.measure_id,
    COUNT(*) AS expected_rows,
    COUNT(r.score) AS scored_rows,
    COUNT(*) - COUNT(r.score) AS missing_score_rows,
    ROUND(100.0 * COUNT(r.score) / COUNT(*), 1) AS score_completeness_pct,
    COUNT(r.denominator) AS rows_with_denominator,
    SUM(CASE WHEN r.footnote IS NOT NULL AND TRIM(r.footnote) <> '' THEN 1 ELSE 0 END) AS rows_with_footnote,
    SUM(CASE WHEN r.compared_to_national = 'Number of Cases Too Small' THEN 1 ELSE 0 END) AS small_case_rows
FROM fact_readmission AS r
GROUP BY r.measure_id
ORDER BY score_completeness_pct, r.measure_id;

-- Join completeness is reported separately because unmatched hospitals are retained.
SELECT
    COUNT(*) AS hospitals,
    SUM(CASE WHEN u.facility_id IS NOT NULL THEN 1 ELSE 0 END) AS county_unmatched_hospitals,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM qa_ambiguous_county_keys AS a WHERE a.county_key = h.county_key
    ) THEN 1 ELSE 0 END) AS ambiguous_key_hospitals,
    SUM(CASE WHEN u.facility_id IS NULL AND NOT EXISTS (
        SELECT 1 FROM qa_ambiguous_county_keys AS a WHERE a.county_key = h.county_key
    ) THEN 1 ELSE 0 END) AS safe_county_matched_hospitals,
    ROUND(100.0 * SUM(CASE WHEN u.facility_id IS NULL AND NOT EXISTS (
        SELECT 1 FROM qa_ambiguous_county_keys AS a WHERE a.county_key = h.county_key
    ) THEN 1 ELSE 0 END) / COUNT(*), 1) AS safe_county_join_coverage_pct
FROM dim_hospital AS h
LEFT JOIN qa_unmatched_hospitals AS u ON u.facility_id = h.facility_id;

-- Q5. COMMUNITY CONTEXT
-- For counties with a meaningful population base, which modeled PLACES estimates
-- coincide with hospital readmission observations? This is contextual, not causal.
SELECT
    c.year,
    c.state,
    c.county,
    c.measure_id AS community_measure,
    ROUND(c.data_value, 1) AS modeled_estimate,
    c.low_ci,
    c.high_ci,
    CAST(c.population AS INTEGER) AS population,
    COUNT(DISTINCT h.facility_id) AS hospital_count,
    COUNT(r.score) AS scored_readmission_rows,
    ROUND(AVG(r.score), 2) AS mean_readmission_score
FROM fact_county_health AS c
LEFT JOIN dim_hospital AS h ON h.county_key = c.county_key
LEFT JOIN fact_readmission AS r ON r.facility_id = h.facility_id
WHERE c.data_value IS NOT NULL
  AND c.population >= 10000
  AND NOT EXISTS (
      SELECT 1
      FROM qa_ambiguous_county_keys AS a
      WHERE a.county_key = c.county_key
        AND a.year = c.year
        AND a.measure_id = c.measure_id
  )
GROUP BY c.year, c.state, c.county, c.county_fips, c.measure_id,
         c.data_value, c.low_ci, c.high_ci, c.population
HAVING COUNT(DISTINCT h.facility_id) > 0
ORDER BY modeled_estimate DESC, c.population DESC
LIMIT 100;
