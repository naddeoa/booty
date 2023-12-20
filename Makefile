project = booty
binary = dist/booty/booty
src = $(shell find $(project) -name '*.py')

.PHONY: all test run run-docker format format-fix lint lint-fix fix debug docker run-docker binary build build-binary build-docker

all: build $(binary)

##
## Build targets
##

build:
	poetry build

build-docker:
	docker build . -t $(project)

build-binary: $(binary)


$(binary): $(src)
	poetry run pyinstaller ./booty/cli.py -n booty

##
## Run targets
##

run:
	poetry run python -m $(project).cli

run-bin:
	$(binary)

run-docker:
	docker run --rm -it $(project)

debug: ## Run the dev server in debug mode
	poetry run python -m debugpy --listen localhost:5678 --wait-for-client -m $(project).cli

test:
	docker build . -t $(project)

##
## Pre commit targets
##

format:
	poetry run ruff format --check

lint:
	poetry run ruff check

format-fix:
	poetry run ruff format

lint-fix:
	poetry run ruff check --fix

fix: format-fix lint-fix

