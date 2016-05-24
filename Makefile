DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DOCKER_MOUNTPOINT     = /salt-toaster
SALT_TESTS            = /salt/src/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(DOCKER_MOUNTPOINT)"


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
ROOT_MOUNTPOINT = /salt-devel
SALT_REPO_MOUNTPOINT = $(ROOT_MOUNTPOINT)/src/
DOCKER_VOLUMES += -v "$(SALT_REPO):$(SALT_REPO_MOUNTPOINT)"
SALT_TESTS = /salt-devel/tests
endif


SALT_TESTS_EXPORT     = "SALT_TESTS=$(SALT_TESTS)"
TOASTER_ROOT_EXPORT   = "TOASTER_ROOT=$(DOCKER_MOUNTPOINT)"
DEVEL_EXPORT          = "DEVEL=$(DEVEL)"
EXPORTS = -e $(SALT_TESTS_EXPORT) -e $(TOASTER_ROOT_EXPORT) -e $(DEVEL_EXPORT)


default: docker_shell

install_salt:
ifeq ($(DEVEL), true)
	zypper --non-interactive in netcat swig gcc-c++
	pip install M2Crypto pyzmq PyYAML pycrypto msgpack-python jinja2 psutil
	pip install -e $(SALT_REPO_MOUNTPOINT)
	pip install rpdb
else
	bin/install_salt.sh
	bin/unpack_salt.sh
endif

fixtures:
ifeq ($(DEVEL), true)
	ln -s $(DOCKER_MOUNTPOINT)/conftest.py $(ROOT_MOUNTPOINT)
else
	ln -s $(DOCKER_MOUNTPOINT)/conftest.py $(cd $SALT_TESTS; pwd)
endif


setup: install_salt fixtures

shell: setup
	/bin/bash

unittests: setup
	py.test -c $(DOCKER_MOUNTPOINT)/unittests.cfg $(SALT_TESTS)

salt_integration_tests: setup
	py.test -c $(DOCKER_MOUNTPOINT)/integration_tests.cfg $(SALT_TESTS)

integration_tests:
	py.test tests/

lastchangelog:
	bin/lastchangelog salt 3

run_unittests: setup unittests lastchangelog

run_salt_integration_tests: setup salt_integration_tests lastchangelog

run_integration_tests: integration_tests lastchangelog

run_tests: setup unittests integration_tests salt_integration_tests lastchangelog

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
