.PHONY: default tests coverage dropcreate

default: tests

tests:
	py.test --doctest-modules --cov-config=coverage.ini --cov-report term --cov-report html --cov shiva tests/ shiva/

debug:
	py.test --pdb --doctest-modules --cov-config=coverage.ini --cov-report term --cov-report html --cov shiva tests/ shiva/

coverage: tests
	python -mwebbrowser -t doc/coverage/index.html


dropcreate:
	rm -f shiva/shiva.db
	python -c "from shiva.app import db; db.create_all()"

