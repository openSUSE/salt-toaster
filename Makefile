DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DEFAULT_FLAVOR        = products
TOASTER_MOUNTPOINT    = /salt-toaster
ROOT_MOUNTPOINT       = /salt/src
SALT_REPO_MOUNTPOINT  = $(ROOT_MOUNTPOINT)/salt-devel
SALT_TESTS            = $(ROOT_MOUNTPOINT)/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(TOASTER_MOUNTPOINT)"
EXPORTS += \
	-e "SALT_TESTS=$(SALT_TESTS)" \
	-e "TOASTER_MOUNTPOINT=$(TOASTER_MOUNTPOINT)" \
	-e "VERSION=$(VERSION)" \
	-e "FLAVOR=$(FLAVOR)" \
	-e "MINION_VERSION=$(MINION_VERSION)" \
	-e "MINION_FLAVOR=$(MINION_FLAVOR)"


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

help:
	@echo "Salt Toaster: an ultimate test suite for Salt."
	@echo
	@echo "Commands:"
	@echo "  set_env              Create environment"
	@echo "  docker_shell         Start Docker shell"
	@echo "  build_image          Build Docker image"
	@echo "  salt_integration     Run Salt integration tests"
	@echo "  custom_integration   Run custom integration tests"
	@echo "  changelog            Show the last three change log entries"
	@echo ""

default: help

set_env:
	bin/prepare_environment.sh --create sandbox

build_image:
ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
	tar --exclude=.git --exclude=.cache --exclude="*.pyc" -cvzf docker/salt.archive -C $(SALT_REPO) .
	VERSION=$(VERSION) FLAVOR=$(FLAVOR) sandbox/bin/python -m build --nopull --nocache
else
	# curl https://codeload.github.com/saltstack/salt/zip/develop > docker/develop.zip
	rm -rf docker/salt.archive
	unzip docker/develop.zip -d docker
	mv docker/salt-develop docker/salt.archive
	VERSION=$(VERSION) FLAVOR=$(FLAVOR) sandbox/bin/python -m build --nopull --nocache
	rm -rf docker/salt.archive
endif
else
	VERSION=$(VERSION) FLAVOR=$(FLAVOR) sandbox/bin/python -m build
endif

install_salt_sources:
	VERSION=$(VERSION) bin/install_salt_sources.sh

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py.source $(ROOT_MOUNTPOINT)/conftest.py

setup: install_salt_sources fixtures

shell: setup
	/bin/bash

salt_master: install_salt_sources
	salt-master -l debug

salt_minion: install_salt_sources
	salt-minion -l debug

salt_unit_tests: setup
	py.test -c $(TOASTER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration: setup
	py.test -c $(TOASTER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

custom_integration: build_image
	py.test -c ./configs/$(VERSION).$(FLAVOR).cfg tests/

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
