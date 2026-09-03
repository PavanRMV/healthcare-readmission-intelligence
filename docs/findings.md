# Executed findings

Generated from the live-run SQLite warehouse. This is a **current CMS extract**, not a historical trend. CDC PLACES values are **modeled county estimates**. Findings are descriptive and do not establish causality.

## Readmission measures

| Measure | Rows | Available | Completeness | Mean score | Denominator-weighted score | Total denominator |
|---|---:|---:|---:|---:|---:|---:|
| READM_30_AMI | 4790 | 1971 | 41.1% | 14.39 | 14.35 | 459524 |
| READM_30_CABG | 4790 | 938 | 19.6% | 11.06 | 10.9 | 126395 |
| READM_30_COPD | 4790 | 3086 | 64.4% | 19.9 | 20.04 | 515451 |
| READM_30_HF | 4790 | 3253 | 67.9% | 21.38 | 21.3 | 1392167 |
| READM_30_HIP_KNEE | 4790 | 1695 | 35.4% | 5.83 | 5.55 | 210031 |
| READM_30_PN | 4790 | 3758 | 78.5% | 17.34 | 17.47 | 1444430 |

Safe county join coverage was **89.4%** (4,847/5,419 hospitals); **544** unmatched and **28** hospitals on ambiguous normalized keys remain visible in QA outputs.

## Descriptive high state/measure averages

Restricted to cells with at least 20 available scores and total denominator ≥1,000. These are comparison prompts, not performance verdicts; case mix and measure specifications matter.

| State | Measure | Available | Mean | Denominator |
|---|---|---:|---:|---:|
| PR | READM_30_HF | 40 | 23.29 | 10376 |
| WV | READM_30_HF | 37 | 22.1 | 10772 |
| MA | READM_30_HF | 53 | 22.03 | 36479 |
| NY | READM_30_HF | 137 | 21.89 | 78545 |
| NH | READM_30_HF | 23 | 21.86 | 6248 |

## Community context

The latest PLACES year in this run is **2023**. The highest modeled estimates below are limited to counties with population ≥10,000 and must not be interpreted as hospital patient prevalence or causes of readmission.

| Measure | County | Modeled estimate | 95% interval | Population | Type |
|---|---|---:|---:|---:|---|
| BPHIGH | Holmes, MS | 53.1 | 48.3–57.6 | 15777 | AgeAdjPrv |
| BPHIGH | Coahoma, MS | 50.7 | 46.0–55.4 | 20077 | AgeAdjPrv |
| BPHIGH | Sunflower, MS | 49.5 | 44.8–53.9 | 24468 | AgeAdjPrv |
| BPHIGH | Washington, MS | 49.4 | 44.8–53.7 | 41946 | AgeAdjPrv |
| BPHIGH | Dallas, AL | 49.2 | 44.7–53.7 | 36165 | AgeAdjPrv |
| BPHIGH | Leflore, MS | 49.2 | 44.9–53.7 | 26378 | AgeAdjPrv |
| BPHIGH | Sumter, AL | 49.1 | 44.5–53.7 | 11727 | AgeAdjPrv |

## HCAHPS availability

HCAHPS contains 325,720 rows; star values are present on 28,647, completed-survey values on 268,532, and response-rate values on 268,532. Use these fields and footnotes when comparing hospitals.
