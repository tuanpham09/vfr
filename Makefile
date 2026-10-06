.PHONY: setup check test-ext fixtures-check verify-list run package
setup:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pre-commit install
check:
	ruff check . && ruff format --check . && mypy core app && lint-imports && python tools/custom_lints.py && pytest -m "not live" -q
test-ext:
	cd extension && npx vitest run
fixtures-check:
	python tools/check_fixtures.py
verify-list:
	grep -rn "\[VERIFY\]" docs AGENTS.md || true
run:
	python -m app.main
package:
	pyinstaller vfr.spec
