install_salt_sources:
	@echo "Installing salt sources"
	VERSION=$(VERSION) bin/install_salt_sources.sh > /salt-toaster/install_salt_sources.log

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py.source $(ROOT_MOUNTPOINT)/conftest.py

remove-upstream-conftest:
	rm -f $(ROOT_MOUNTPOINT)/salt-*/tests/conftest.py

setup: install_salt_sources fixtures remove-upstream-conftest

default: setup
	$(CMD)

changelog:
	/root/bin/lastchangelog salt 3

tests: default changelog
