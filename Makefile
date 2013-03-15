.PHONY: default tests coverage

default: tests

tests:
	py.test --doctest-modules --cov-config=coverage.ini --cov-report term --cov-report html --cov shiva tests/ shiva/

debug:
	py.test --pdb --doctest-modules --cov-config=coverage.ini --cov-report term --cov-report html --cov shiva tests/ shiva/

coverage: tests
	python -mwebbrowser -t doc/coverage/index.html


