project = booty

.PHONY: all test run run-docker format format-fix lint lint-fix fix debug docker run-docker

all:
	poetry build

test:
	docker build . -t $(project)

run:
	poetry run python -m $(project).main

docker:
	docker build . -t $(project)

run-docker:
	docker run --rm -it $(project)

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
	poetry run python -m debugpy --listen localhost:5678 --wait-for-client -m $(project).cli
