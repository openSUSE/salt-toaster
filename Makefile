DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DOCKER_MOUNTPOINT     = /salt-toaster
SALT_MOUNTPOINT       = /usr/lib/python2.7/site-packages/salt/
SALT_TESTS            = /salt/src/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(DOCKER_MOUNTPOINT)"
SALT_TESTS_EXPORT     = "SALT_TESTS=$(SALT_TESTS)"
TOASTER_ROOT_EXPORT   = "TOASTER_ROOT=$(DOCKER_MOUNTPOINT)"
DEVEL_EXPORT          = "DEVEL=$(DEVEL)"
EXPORTS = -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) -e $(DEVEL_EXPORT)


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
	DOCKER_VOLUMES += \
	 -v "$(CURDIR)/mount/salt/salt:$(SALT_MOUNTPOINT)" \
	 -v "$(CURDIR)/mount/tests:/salt/src/"
endif


default: docker_shell

install_salt:
	bin/install_salt.sh
	bin/unpack_salt.sh

fixtures:
	bin/link_fixtures.sh

shell: install_salt fixtures
	/bin/bash

unittests: install_salt fixtures
	py.test -c $(DOCKER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration_tests: install_salt fixtures
	py.test -c $(DOCKER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

integration_tests:
	py.test tests/

lastchangelog:
	bin/lastchangelog salt 3

run_unittests: install_salt fixtures unittests lastchangelog

run_salt_integration_tests: install_salt fixtures salt_integration_tests lastchangelog

run_integration_tests: integration_tests lastchangelog

run_tests: install_salt fixtures unittests integration_tests salt_integration_tests lastchangelog

jenkins_run_unittests: run_unittests

jenkins_run_salt_integration_tests: run_salt_integration_tests

jenkins_run_integration_tests: run_integration_tests

jenkins_run_tests: run_tests

docker_shell ::
	docker run -p 4444:4444 -t -i $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) shell

docker_pull ::
	docker pull $(DOCKER_IMAGE)

docker_run_unittests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_unittests

docker_run_salt_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_salt_integration_tests

docker_run_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_integration_tests

docker_run_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_tests

docker_jenkins_run_unittests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_unittests

docker_jenkins_salt_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_salt_integration_tests

docker_jenkins_integration_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_integration_tests

docker_jenkins_run_tests ::
	docker run $(EXPORTS) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_tests
