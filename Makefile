DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
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
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(VERSION)
endif


ifeq ($(DEVEL), true)
	DOCKER_VOLUMES += -v "$(SALT_REPO):$(SALT_REPO_MOUNTPOINT)"
	EXPORTS += -e "SALT_REPO_MOUNTPOINT=$(SALT_REPO_MOUNTPOINT)"
else
	DEVEL = false
endif



default: docker_shell

install_salt:
	bin/install_salt.sh

fixtures:
	ln -s $(TOASTER_MOUNTPOINT)/conftest.py $(ROOT_MOUNTPOINT)

setup: install_salt fixtures

shell: setup
	/bin/bash

salt_unit_tests: setup
	py.test -c $(TOASTER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration_tests: setup
	py.test -c $(TOASTER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

custom_integration_tests: setup
	py.test tests/

lastchangelog:
	bin/lastchangelog salt 3

run_salt_unit_tests: salt_unit_tests lastchangelog

run_salt_integration_tests: salt_integration_tests lastchangelog

run_custom_integration_tests: custom_integration_tests lastchangelog

run_tests: salt_unit_tests custom_integration_tests salt_integration_tests lastchangelog

docker_shell ::
	docker run -p 4444:4444 -t -i $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) shell

docker_pull ::
	docker pull $(DOCKER_IMAGE)

docker_run_salt_unit_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_salt_unit_tests

docker_run_salt_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_salt_integration_tests

docker_run_custom_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_custom_integration_tests

docker_run_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(TOASTER_MOUNTPOINT) run_tests
