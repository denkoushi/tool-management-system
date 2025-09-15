.PHONY: run dev db-up db-down fmt

run:
	python -m app.main

dev:
	FLASK_ENV=development python -m app.main

db-up:
	docker compose up -d

db-down:
	docker compose down

fmt:
	@echo "No formatter configured; skipping"

