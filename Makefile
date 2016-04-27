SALT_TESTS            = /salt/src/salt-*/tests
DOCKER_IMAGE          = toaster-sles12sp1
DOCKER_MOUNTPOINT     = /salt-toaster
DOCKER_REGISTRY       = suma-docker-registry.suse.de
SALT_TESTS_EXPORT     = "SALT_TESTS=$(SALT_TESTS)"
TOASTER_ROOT_EXPORT   = "TOASTER_ROOT=$(DOCKER_MOUNTPOINT)"
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(DOCKER_MOUNTPOINT)"


link_fixtures:
	bin/link_fixtures.sh

shell: link_fixtures
	/bin/bash

run_unit_tests: link_fixtures
	py.test -c $(DOCKER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

update:
	/root/install_salt.sh

jenkins_unittests: update run_unit_tests


docker_shell ::
	docker run -t -i -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) shell

docker_run_unittests-sles12sp1 ::
	docker run -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) make -C $(DOCKER_MOUNTPOINT) run_unit_tests
