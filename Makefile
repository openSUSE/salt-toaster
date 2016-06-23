DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DEFAULT_FLAVOR        = products
TOASTER_MOUNTPOINT    = /salt-toaster
ROOT_MOUNTPOINT       = /salt/src
SALT_REPO_MOUNTPOINT  = $(ROOT_MOUNTPOINT)/salt-devel
SALT_TESTS            = $(ROOT_MOUNTPOINT)/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(TOASTER_MOUNTPOINT)"
EXPORTS += \
	-e "DEVEL=$(DEVEL)" \
	-e "SALT_TESTS=$(SALT_TESTS)" \
	-e "TOASTER_MOUNTPOINT=$(TOASTER_MOUNTPOINT)"


ifndef DOCKER_IMAGE
	ifndef DOCKER_REGISTRY
		DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
	endif
	ifndef VERSION
		VERSION = $(DEFAULT_VERSION)
	endif
	ifndef FLAVOR
		FLAVOR = $(DEFAULT_FLAVOR)
	endif
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(VERSION)-$(FLAVOR)
endif


ifeq ($(DEVEL), true)
	DOCKER_VOLUMES += -v "$(SALT_REPO):$(SALT_REPO_MOUNTPOINT)"
	EXPORTS += -e "SALT_REPO_MOUNTPOINT=$(SALT_REPO_MOUNTPOINT)"
else
	DEVEL = false
endif

help:
	@echo "Salt Toaster: an ultimate test suite for Salt.\n\nCommands:"
	@echo "\tdocker_shell\t\tStart Docker shell."
	@echo "\tbuild_image\t\tBuild Docker image."
	@echo "\tsalt_integration\tRun Salt integration tests"
	@echo "\tcustom_integration\tRun custom integration tests"
	@echo "\tchangelog\t\tShow the last three change log entries"
	@echo ""

default: help

build_image:
	VERSION=$(VERSION) FLAVOR=$(FLAVOR) python -m build --nocache

install_salt:
	bin/install_salt.sh

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py.source $(ROOT_MOUNTPOINT)/conftest.py

setup: install_salt fixtures

shell: setup
	/bin/bash

salt_master: install_salt
	salt-master -l debug

salt_minion: install_salt
	salt-minion -l debug

salt_unit_tests: setup
	py.test -c $(TOASTER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration: setup
	py.test -c $(TOASTER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

custom_integration_tests: build_image
	VERSION=$(VERSION) FLAVOR=$(FLAVOR) py.test tests/

changelog:
	docker/bin/lastchangelog salt 3

run_salt_unit_tests: salt_unit_tests changelog

run_salt_integration_tests: salt_integration changelog

docker_shell :: build_image
	docker run -p 4444:4444 -t -i $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) shell

docker_pull ::
	docker pull $(DOCKER_IMAGE)

docker_run_salt_unit_tests :: build_image
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_salt_unit_tests

docker_run_salt_integration_tests :: build_image
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_salt_integration_tests
