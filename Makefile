.PHONY: test init serve evaluate audit scan
test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
init:
	PYTHONPATH=src python3 -m ops_copilot.cli init
serve:
	PYTHONPATH=src python3 -m ops_copilot.cli serve
evaluate:
	PYTHONPATH=src python3 -m ops_copilot.cli evaluate
audit:
	PYTHONPATH=src python3 -m ops_copilot.cli audit
scan:
	python3 scripts/check_release.py
