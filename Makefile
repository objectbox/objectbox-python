VENV = .venv
export VIRTUAL_ENV := $(abspath ${VENV})
export PATH := ${VIRTUAL_ENV}/bin:${PATH}

################################

${VENV}: ${VENV}/bin/activate

${VENV}/bin/activate: requirements.txt
	test -d ${VENV} || virtualenv ${VENV}
	# remove packages not in the requirements.txt
	pip freeze | grep -v -f requirements.txt - | grep -v '^#' | grep -v '^-e ' | xargs pip uninstall -y || echo "never mind"
    # install and upgrade based on the requirements.txt
	pip install --upgrade -r requirements.txt
	# let make know this is the last time requirements changed
	touch ${VENV}/bin/activate

init: ${VENV}

.PHONY: init