# Methodology and limitations

## Cohort and measures
The run uses each source's current live publication. CMS readmissions are filtered to AMI, CABG, COPD, heart failure, hip/knee, and pneumonia 30-day measures. Scores marked `Not Available` are NULL and stay in completeness denominators. Facility ID is left-padded to six characters and stored as text.

CDC data is county-level PLACES output for COPD, CHD, DIABETES, CSMOKING, BPHIGH, ACCESS2, and GHLTH. Within county/year/measure, age-adjusted prevalence (`AgeAdjPrv`) is selected when available, otherwise crude prevalence (`CrdPrv`). Confidence limits and population are retained.

## Interpretation guardrails
- Current extracts cannot establish historical trends.
- CDC PLACES values are modeled county estimates, subject to model and survey uncertainty; they are not hospital-patient measurements.
- County context does not imply that a given patient has a condition (ecological fallacy).
- Associations are descriptive, not causal; no risk adjustment or causal identification is performed.
- Hospital means can be misleading where denominators are missing or differ. Reports show denominator-weighted values and completeness when possible.
- HCAHPS response rates and completed survey counts should accompany comparisons; nonresponse and case-mix matter.
- Normalized-name joins can fail for independent cities and unusual county labels. Unmatched records are never silently discarded.

## Reproducibility
Raw SHA-256, resolved URLs, CMS publication dates, retrieval timestamps, bytes, and rows are persisted. Reruns may differ because publishers update live datasets.
