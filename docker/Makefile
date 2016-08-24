install_salt_sources:
	@echo "Installing salt sources"
	VERSION=$(VERSION) bin/install_salt_sources.sh > /salt-toaster/install_salt_sources.log

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py.source $(ROOT_MOUNTPOINT)/conftest.py

setup: install_salt_sources fixtures

shell: setup
	/bin/bash

salt_unit_tests: setup
	py.test -c $(TOASTER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS) --junitxml=junit.report.xml

salt_integration: setup
	py.test -c $(TOASTER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS) --junitxml=junit.report.xml

changelog:
	docker/bin/lastchangelog salt 3

run_salt_unit_tests: salt_unit_tests changelog

run_salt_integration_tests: salt_integration changelog
