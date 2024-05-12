SHELL := /bin/bash
VENV = .venv
VENVBIN = ${VENV}/bin
PYTHON = python3
PIP = ${PYTHON} -m pip

# Detect windows - works on both 32 & 64-bit windows
ifeq ($(OS),Windows_NT)
VENVBIN = ${VENV}/Scripts
endif

export PATH := $(abspath ${VENVBIN}):${PATH}


.PHONY: init test build benchmark publish venv-init

# Default target executed when no arguments are given to make.
default_target: build test

help:				## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

################################

all: depend build test	## Get dependencies, clean, build and test

build: ${VENV} clean	## Clean and build
	set -e ; \
	${PYTHON} setup.py bdist_wheel ; \
	ls -lh dist

${VENV}: ${VENVBIN}/activate

venv-init:
	${PIP} install --user virtualenv
	${PYTHON} -m virtualenv ${VENV}

# 	remove packages not in the requirements.txt
# 	install and upgrade based on the requirements.txt
# 	let make know this is the last time requirements changed
${VENVBIN}/activate: requirements.txt
	set -e ; \
	if [ ! -d "${VENV}" ] ; then make venv-init ; fi ; \
	${PIP} freeze | grep -v -f requirements.txt - | grep -v '^#' | grep -v '^-e ' | xargs ${PIP} uninstall -y || echo "never mind" ; \
	${PIP} install --upgrade -r requirements.txt ; \
	touch ${VENVBIN}/activate

depend:	${VENV}			## Prepare dependencies
	set -e ; \
	${PYTHON} download-c-lib.py

test: ${VENV}			## Test all targets
	set -e ; \
	${PYTHON} -m pytest --capture=no --verbose

benchmark: ${VENV}		## Run CRUD benchmarks
	set -e ; \
	${PYTHON} -m benchmark

clean:					## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

publish:				## Publish the package built by `make build`
	set -e
	@echo "****************************************************************"
	@echo ">>>  Please enter the API token when asked for a password.  <<<"
	@echo ">>>  The API token starts with the prefix 'pypi-'.          <<<"
	@echo ">>>  See https://pypi.org/help/#apitoken for details.       <<<"
	@echo "****************************************************************"
	${PYTHON} -m twine upload -u "__token__" --verbose dist/objectbox*.whl
