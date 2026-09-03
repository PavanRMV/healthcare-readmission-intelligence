# Power BI project

Open [`Healthcare Readmission Intelligence.pbip`](pbip/Healthcare%20Readmission%20Intelligence.pbip) with Power BI Desktop.

## First refresh after cloning

The source-controlled semantic model intentionally contains no username-specific absolute path.

1. From the repository root, install the package and generate the analytical exports:
   ```bash
   python -m pip install -e ".[dev]"
   python -m healthcare_intelligence.pipeline --root .
   ```
2. Open `powerbi/pbip/Healthcare Readmission Intelligence.pbip`.
3. In **Transform data → Manage parameters**, set `ProjectRoot` to the cloned repository's absolute root directory.
4. Apply the parameter and select **Refresh**.

The generated CSV facts remain outside Git because they are reproducible and would unnecessarily inflate the repository.

## Report pages

- **Executive Overview** — hospital coverage, score completeness, fixed heart-failure readmission rate, nurse communication, state benchmarks, and hospital ratings.
- **Hospital Opportunity** — state and hospital slicers with fixed, clinically coherent readmission and patient-experience measures.
- **Data Quality / Provenance** — completeness, unmatched geography, safe county coverage, warehouse QA, and source URLs.

## Analytical safeguards

- Readmission measures are never combined into one heterogeneous clinical score.
- Percentage-point source values are divided by 100 before Power BI percentage formatting.
- Repeated HCAHPS survey counts aggregate once per hospital.
- Ambiguous normalized county keys are excluded from geographic context joins.
- Missing and suppressed CMS values remain blank rather than being converted to zero.

## Source-control validation

The PBIP uses PBIR report metadata and a TMDL semantic model. Validate it with:

```bash
powerbi-report-author validate "powerbi/pbip/Healthcare Readmission Intelligence.pbip" --format text
```

`generate_project.py` reproducibly rebuilds the report metadata from repository-local assets.
