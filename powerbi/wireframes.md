# Page wireframes

## 1 Executive overview
Top cards: hospitals, available score rows, score completeness, county join coverage. Bar charts: denominator-weighted score **by measure** and completeness by measure. Matrix: measure by state with score and completeness. Never show an all-condition composite score. Banner: current extract only; descriptive, not trend/causal.

## 2 Hospital opportunity
Slicers: state, measure, ownership, hospital type. Ranked table: facility, score, denominator, same-state/same-measure gap, comparison, footnote. Scatter: overall rating vs score for **one selected readmission measure**; size by denominator. Suppress interpretation where score/denominator unavailable.

## 3 Community context
Map/heatmap: CDC modeled estimate by county and measure with CI tooltip. Adjacent hospital readmission distribution. Subtitle explicitly says modeled county estimate; no patient-level or causal interpretation.

## 4 Patient experience
HCAHPS star/answer metrics with completed surveys and response-rate tooltips; facility drill-through.

## 5 Data quality & provenance
Completeness by measure; unmatched county table; source IDs, resolved URLs, release/retrieval dates, raw rows and SHA-256.
