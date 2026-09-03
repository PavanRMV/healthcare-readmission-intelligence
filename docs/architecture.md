# Architecture

```text
CMS metastore -> resolved CSVs --\
                                  -> Python cleaning/QA -> SQLite -> analytical SQL -> CSV -> Power BI
CDC Socrata API -> JSON ---------/                      \-> unmatched join report
```

## Layers
1. **Raw snapshot**: exact downloaded CMS CSVs and CDC JSON (gitignored), hashed in `source_snapshot`.
2. **Standardization**: six-character Facility ID text, safe numeric parsing, normalized county key, explicit measure filters.
3. **Warehouse**: `dim_hospital`, readmission/HCAHPS/county health facts, metadata, QA rejects, indexes, joined view.
4. **Serving**: curated CSVs retain observation denominators, confidence intervals, survey sample fields, and missing rows.

County key algorithm: uppercase state + `|` + Unicode-to-ASCII county name; strip County/Parish/Borough/Census Area/Municipality and punctuation. This is transparent but imperfect, so every unmatched hospital is exported.
