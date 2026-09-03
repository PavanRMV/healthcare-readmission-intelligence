# Power BI model and build guide

## Import
Import these UTF-8 CSVs from `outputs/`: `dim_hospital`, `fact_readmission`, `fact_hcahps`, `fact_county_health`, `qa_unmatched_hospitals`, `qa_ambiguous_county_keys`, and `source_snapshot`. Explicitly set `facility_id` to Text before applying changes so leading zeros remain. Set county FIPS to Text.

## Star schema
- `dim_hospital[facility_id]` 1:* `fact_readmission[facility_id]`
- `dim_hospital[facility_id]` 1:* `fact_hcahps[facility_id]`
- Use a bridge/deduplicated `DimCounty[county_key]` for hospital-to-county health relationships; do not directly many-to-many join facts. Exclude keys listed in `qa_ambiguous_county_keys.csv`: normalization can collapse distinct county FIPS (for example, county/city equivalents), and the SQLite joined view deliberately leaves those community fields null rather than duplicating hospital rows.
- Optional `DimMeasure` separates CMS readmission and CDC risk measure labels.

Filter direction should be single from dimensions to facts. Mark PLACES visuals/subtitles “Modeled county estimates.” Keep every readmission score visual in a single-measure context; condition-specific scores must not be averaged into one hospital KPI.

## HCAHPS grain warning
`completed_surveys` and `response_rate` repeat on the measure rows for a hospital. A raw `SUM(fact_hcahps[completed_surveys])` therefore overcounts the survey base. Use the facility-grain `SUMX/AVERAGEX` measures in `measures.dax`, which take one `MAX` value per visible hospital, and use the explicitly filtered summary-star measure for score cards.

## Build sequence
1. Import and set types; hide technical keys except drill-through pages.
2. Apply `theme.json`; create measures from `measures.dax`.
3. Build pages from `wireframes.md`.
4. Add source date and completeness cards to every analytical page.
5. Add tooltip fields: denominator/patient counts, footnotes, confidence interval, response rate/completed surveys.
6. Validate totals against `outputs/run_summary.json` and `data_quality.csv`.

A `.pbix` is intentionally not included because Power BI Desktop generation is not available in the automated environment.
