
.PHONY: all

all:
	poetry run python -m systemconf.main

test:
	docker build . -t systemconf

run:
	docker run --rm -it systemconf

format:
	poetry run ruff format --check

format-fix:
	poetry run ruff format

lint:
	poetry run ruff check

lint-fix:
	poetry run ruff check --fix

fix: format-fix lint-fix

debug: ## Run the dev server in debug mode
	poetry run python -m debugpy --listen localhost:5678 --wait-for-client -m systemconf.main
