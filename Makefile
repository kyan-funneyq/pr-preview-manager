PYTHON ?= python3
VENV := .venv
DEMO_ROOT := .preview-root

.PHONY: setup verify demo demo-build clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install -q -r requirements-dev.txt

verify:
	$(VENV)/bin/python -m ruff check .
	$(VENV)/bin/python -m pytest -q

demo-build:
	rm -rf dist $(DEMO_ROOT)
	$(PYTHON) src/build_site.py --pr 1 --sha a1b2c3d --out dist/pr-1
	$(PYTHON) src/previewctl.py prepare --pr 1 --sha a1b2c3d --source dist/pr-1 --target $(DEMO_ROOT)
	$(PYTHON) src/build_site.py --pr 2 --sha e4f5a6b --out dist/pr-2
	$(PYTHON) src/previewctl.py prepare --pr 2 --sha e4f5a6b --source dist/pr-2 --target $(DEMO_ROOT)
	$(PYTHON) src/previewctl.py status --target $(DEMO_ROOT)

demo: demo-build
	@echo "Open http://localhost:8000/pr-preview/pr-1/ and http://localhost:8000/pr-preview/pr-2/ (Ctrl+C to stop)"
	$(PYTHON) -m http.server 8000 --directory $(DEMO_ROOT)

clean:
	rm -rf dist $(DEMO_ROOT)
