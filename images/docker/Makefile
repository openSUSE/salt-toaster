PYTHON_CMD:=$(shell which python 2>/dev/null || which python3 2>/dev/null)
ifeq ("$(NOX)", "False")
CONFTEST_SOURCE=$(TOASTER_MOUNTPOINT)/conftest_source_legacy.py
else
CONFTEST_SOURCE=$(TOASTER_MOUNTPOINT)/conftest_source_nox.py
endif

install_salt_sources:
	@echo "Installing salt sources"
	DISTRO=$(DISTRO) bin/install_salt_sources.sh > /salt-toaster/install_salt_sources.log

fixtures:
	ln -s $(CONFTEST_SOURCE)  $(ROOT_MOUNTPOINT)/conftest.py

remove-upstream-conftest:
ifeq ("$(NOX)", "False")
	# everything
	find $(ROOT_MOUNTPOINT) -name conftest.py -delete
else
	# down to ROOT_MOUNTPOINT/salt-xyz/tests
	find $(ROOT_MOUNTPOINT) -maxdepth 3 -name conftest.py -delete
endif

setup: install_salt_sources remove-upstream-conftest fixtures

default: setup
	$(CMD)

changelog:
	$(PYTHON_CMD) /root/bin/lastchangelog salt 3

ifneq (,$(findstring ubuntu,$(DISTRO)))
tests: default
else ifneq (,$(findstring devel,$(FLAVOR)))
tests: default
else
tests: default changelog
endif
