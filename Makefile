VENV = .venv
export PATH := $(abspath ${VENV})/bin:${PATH}

.PHONY: init test build benchmark

# Default target executed when no arguments are given to make.
default_target: all

help:				## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

################################

all: depend build test	## Prepare, build and test

build: ${VENV} clean	## Build and clean
	python3 setup.py bdist_wheel
	ls -lh dist

${VENV}: ${VENV}/bin/activate

${VENV}/bin/activate: requirements.txt
	test -d ${VENV} || virtualenv ${VENV}
	# remove packages not in the requirements.txt
	pip3 freeze | grep -v -f requirements.txt - | grep -v '^#' | grep -v '^-e ' | xargs pip3 uninstall -y || echo "never mind"
    # install and upgrade based on the requirements.txt
	pip3 install --upgrade -r requirements.txt
	# let make know this is the last time requirements changed
	touch ${VENV}/bin/activate

depend:	${VENV}			## Prepare dependencies
	python3 download-c-lib.py

test: ${VENV}			## Test all targets
	python3 -m pytest --capture=no --verbose

benchmark: ${VENV}		## Run CRUD benchmarks
	python3 -m benchmark

clean:					## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
