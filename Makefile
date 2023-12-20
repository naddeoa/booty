project = booty
binary = dist/booty/booty
src = $(shell find $(project) -name '*.py')

.PHONY: all test run run-docker format format-fix lint lint-fix fix debug docker run-docker binary build build-binary build-docker

all: build $(binary)

##
## Build targets
##

build:  # Build dist wheels
	poetry build

build-docker:  # Build the test docker image.
	docker build . -t $(project)

build-docker-base:  ## Build the base docker image for integ testing.
	docker build . -f Dockerfile.base -t naddeoa/booty:ubuntu22.04

build-binary: $(binary)  # Build the binary variant of booty via pyinstaller.


$(binary): $(src)
	poetry run pyinstaller ./booty/cli.py -n booty -y

##
## Run targets
##

run:  ## Run the project python diriectly
	poetry run python -m $(project).cli

run-bin:  ## Run the generated binary.
	$(binary)

run-docker:  ## Run the test docker image from build-docker.
	docker run --rm -it $(project)

debug: ## Run booty in debug mode via debugpy.
	poetry run python -m debugpy --listen localhost:5678 --wait-for-client -m $(project).cli

test:
	poetry run pytest

##
## Pre commit targets
##

format:  ## Run the ruff formatter.
	poetry run ruff format --check

lint:  ## Run the ruff linter.
	poetry run ruff check

format-fix:  ## Run the ruff formatter.
	poetry run ruff format

lint-fix:  ## Run the ruff linter.
	poetry run ruff check --fix

fix: format-fix lint-fix  ## Run the ruff formatter and linter.

help: ## Show this help message.
	@echo 'usage: make [target] ...'
	@echo
	@echo 'targets:'
	@egrep '^(.+)\:(.*) ##\ (.+)' ${MAKEFILE_LIST} | sed -s 's/:\(.*\)##/: ##/' | column -t -c 2 -s ':#'

