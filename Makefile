install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

pipeline:
	python -m healthcare_intelligence.pipeline --root .

report:
	python -m healthcare_intelligence.reporting --db data/warehouse/healthcare.db --output-dir outputs/reporting

acceptance: test report
	python -m compileall -q src
