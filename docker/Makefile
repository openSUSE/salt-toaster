install_salt_sources:
	@echo "Installing salt sources"
	VERSION=$(VERSION) bin/install_salt_sources.sh > /salt-toaster/install_salt_sources.log

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py.source $(ROOT_MOUNTPOINT)/conftest.py

setup: install_salt_sources fixtures

default: setup
	$(CMD)

changelog:
	docker/bin/lastchangelog salt 3

tests: default changelog
