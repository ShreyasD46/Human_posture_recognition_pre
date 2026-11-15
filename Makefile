.PHONY: benchmark test run clean install help

help:
	@echo "Available commands:"
	@echo "  make benchmark   Run Pi 4B latency, FPS, memory and thermal profiler"
	@echo "  make test        Run complete test suite (unit + regression + replay)"
	@echo "  make run         Start local development server"
	@echo "  make install     Install local dependencies"

benchmark:
	backend/venv/Scripts/python.exe deploy/scripts/benchmark.py || python3 deploy/scripts/benchmark.py

test:
	backend/venv/Scripts/python.exe -m pytest tests/ backend/tests/ -v || python3 -m pytest tests/ backend/tests/ -v

run:
	backend/venv/Scripts/python.exe backend/app.py || python3 backend/app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
