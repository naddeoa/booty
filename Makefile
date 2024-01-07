project = booty
binary = dist/booty/booty
src = $(shell find $(project) -name '*.py')

.PHONY: all test run run-docker format format-fix lint lint-fix fix debug docker run-docker build build-docker
.PHONY: build-binary-linux build-binary-mac build-docker-base clean

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

clean:
	rm -rf dist

build-binary-linux:  # Build the binary variant of booty via pyinstaller for linux.
	poetry run pyinstaller ./booty/cli.py -n booty_linux_x86_64 -y \
		--add-data="./booty/lang/:./booty/lang/" \
		--exclude-module pandas \
		--exclude-module numpy \
		--exclude-module pytest \
		--exclude-module pygments \
		--onefile \
		--strip \
		--exclude-module multiprocessing.util

build-binary-mac:  # Build the binary variant of booty via pyinstaller for mac.
	poetry run pyinstaller ./booty/cli.py -n booty_mac_x86_64 -y \
		--add-data="./booty/lang/:./booty/lang/" \
		--target-arch x86_64 \
		--exclude-module pandas \
		--exclude-module numpy \
		--exclude-module pytest \
		--exclude-module pygments \
		--onefile \
		--strip \
		--exclude-module multiprocessing.util

build-binary-mac-arm:  # Build the binary variant of booty via pyinstaller for arm mac.
	poetry run pyinstaller ./booty/cli.py -n booty_mac_arm64 -y \
		--add-data="./booty/lang/:./booty/lang/" \
		--target-arch arm64 \
		--exclude-module pandas \
		--exclude-module numpy \
		--exclude-module pytest \
		--exclude-module pygments \
		--onefile \
		--strip \
		--exclude-module multiprocessing.util

build-binary-mac-universal:  # Build the binary variant of booty via pyinstaller for arm mac.
	poetry run pyinstaller ./booty/cli.py -n booty_mac_universal -y \
		--add-data="./booty/lang/:./booty/lang/" \
		--target-arch universal2 \
		--exclude-module pandas \
		--exclude-module numpy \
		--exclude-module pytest \
		--exclude-module pygments \
		--onefile \
		--strip \
		--exclude-module multiprocessing.util

##
## Version targets
##
bump-patch: ## Bump the patch version (_._.X) everywhere it appears in the project
	@$(call i, Bumping the patch number)
	poetry run bumpversion patch --allow-dirty

bump-minor: ## Bump the minor version (_.X._) everywhere it appears in the project
	@$(call i, Bumping the minor number)
	poetry run bumpversion minor --allow-dirty

bump-major: ## Bump the major version (X._._) everywhere it appears in the project
	@$(call i, Bumping the major number)
	poetry run bumpversion major --allow-dirty

bump-release: ## Convert the version into a release variant (_._._) everywhere it appears in the project
	@$(call i, Removing the dev build suffix)
	poetry run bumpversion release --allow-dirty

bump-build: ## Bump the build number (_._._-____XX) everywhere it appears in the project
	@$(call i, Bumping the build number)
	poetry run bumpversion build --allow-dirty


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

