DEFAULT_REGISTRY      = suma-docker-registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DOCKER_MOUNTPOINT     = /salt-toaster
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(DOCKER_MOUNTPOINT)"
SALT_TESTS            = /salt/src/salt-*/tests
SALT_TESTS_EXPORT     = "SALT_TESTS=$(SALT_TESTS)"
TOASTER_ROOT_EXPORT   = "TOASTER_ROOT=$(DOCKER_MOUNTPOINT)"


ifndef DOCKER_IMAGE
	ifndef DOCKER_REGISTRY
		DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
	endif
	ifndef VERSION
		VERSION = $(DEFAULT_VERSION)
	endif
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(VERSION)
endif


default: docker_shell

update:
	/root/install_salt.sh

fixtures:
	bin/link_fixtures.sh

shell: fixtures
	/bin/bash

unittests: fixtures
	py.test -c $(DOCKER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration_tests: fixtures
	py.test -c $(DOCKER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

integration_tests:
	py.test

lastchangelog:
	bin/lastchangelog salt 1

run_unittests: fixtures unittests lastchangelog

run_salt_integration_tests: fixtures salt_integration_tests lastchangelog

run_integration_tests: integration_tests lastchangelog

run_tests: fixtures unittests integration_tests salt_integration_tests lastchangelog

jenkins_run_unittests: update run_unittests

jenkins_run_salt_integration_tests: update run_salt_integration_tests

jenkins_run_integration_tests: update run_integration_tests

jenkins_run_tests: update run_tests

docker_shell ::
	docker run -t -i -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) shell

docker_pull ::
	docker pull $(DOCKER_IMAGE)

docker_run_unittests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_unittests

docker_run_salt_integration_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_salt_integration_tests

docker_run_integration_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_integration_tests

docker_run_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_tests

docker_jenkins_run_unittests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_unittests

docker_jenkins_salt_integration_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_salt_integration_tests

docker_jenkins_integration_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_integration_tests

docker_jenkins_run_tests ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) jenkins_run_tests
