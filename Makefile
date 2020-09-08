VENV = .venv
export VIRTUAL_ENV := $(abspath ${VENV})
export PATH := ${VIRTUAL_ENV}/bin:${PATH}

################################

build: ${VENV} clean
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

init: ${VENV}

test: ${VENV}
	python3 -m pytest -s

benchmark: ${VENV}
	python3 -m benchmark

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

.PHONY: init test build benchmark