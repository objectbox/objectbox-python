VENV = .venv
VENVBIN = ${VENV}/bin

# Detect windows - works on both 32 & 64-bit windows
ifeq ($(OS),Windows_NT)
VENVBIN = ${VENV}/Scripts
endif

export PATH := $(abspath ${VENVBIN}):${PATH}


.PHONY: init test build benchmark publish

# Default target executed when no arguments are given to make.
default_target: build test

help:				## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

################################

all: depend build test	## Get dependencies, clean, build and test

build: ${VENV} clean	## Clean and build
	python setup.py bdist_wheel
	ls -lh dist

${VENV}: ${VENVBIN}/activate

${VENVBIN}/activate: requirements.txt
	virtualenv ${VENV}
# 	remove packages not in the requirements.txt
	pip3 freeze | grep -v -f requirements.txt - | grep -v '^#' | grep -v '^-e ' | xargs pip3 uninstall -y || echo "never mind"
# 	install and upgrade based on the requirements.txt
	python -m pip install --upgrade -r requirements.txt
# 	let make know this is the last time requirements changed
	touch ${VENVBIN}/activate

depend:	${VENV}			## Prepare dependencies
	python download-c-lib.py

test: ${VENV}			## Test all targets
	python -m pytest --capture=no --verbose

benchmark: ${VENV}		## Run CRUD benchmarks
	python -m benchmark

clean:					## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

publish:				## Publish the package built by `make build`
	python -m twine upload --verbose dist/objectbox*.whl