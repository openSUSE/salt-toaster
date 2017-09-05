DEFAULT_REGISTRY      = registry.mgr.suse.de
DEFAULT_VERSION       = sles12sp1
DEFAULT_FLAVOR        = products
TOASTER_MOUNTPOINT    = /salt-toaster
ROOT_MOUNTPOINT       = /salt/src
SALT_REPO_MOUNTPOINT  = $(ROOT_MOUNTPOINT)/salt-devel
SALT_TESTS            = $(ROOT_MOUNTPOINT)/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(TOASTER_MOUNTPOINT)"

ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
$(eval DOCKER_VOLUMES:=$(DOCKER_VOLUMES) -v $(SALT_REPO):$(SALT_REPO_MOUNTPOINT))
endif
endif

EXPORTS += \
	-e "SALT_TESTS=$(SALT_TESTS)" \
	-e "VERSION=$(VERSION)" \
	-e "FLAVOR=$(FLAVOR)" \
	-e "DOCKER_IMAGE=$(DOCKER_IMAGE)" \
	-e "DOCKER_FILE=$(DOCKER_FILE)" \
	-e "MINION_VERSION=$(MINION_VERSION)" \
	-e "MINION_FLAVOR=$(MINION_FLAVOR)" \
	-e "ROOT_MOUNTPOINT=$(ROOT_MOUNTPOINT)" \
	-e "SALT_REPO_MOUNTPOINT=$(SALT_REPO_MOUNTPOINT)" \
	-e "TOASTER_MOUNTPOINT=$(TOASTER_MOUNTPOINT)"

ifndef DOCKER_REGISTRY
	DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
endif

ifndef VERSION
	VERSION = $(DEFAULT_VERSION)
endif

ifndef FLAVOR
	FLAVOR = $(DEFAULT_FLAVOR)
endif

ifndef DOCKER_IMAGE
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(VERSION)-$(FLAVOR)
endif

ifndef DOCKER_FILE
	DOCKER_FILE = Dockerfile.$(VERSION).$(FLAVOR)
endif

help:
	@echo "Salt Toaster: an ultimate test suite for Salt."
	@echo
	@echo "Commands:"
	@echo "  set_env                 Create environment"
	@echo "  docker_shell            Start Docker shell"
	@echo "  saltstack.integration   Run Salt integration tests"
	@echo "  saltstack.unit          Run Salt unit tests"
	@echo "  suse.integration        Run SUSE custom integration tests"
	@echo ""

default: help

set_env:
	bin/prepare_environment.sh --create sandbox

pull_image:
ifndef NOPULL
	docker pull $(DOCKER_IMAGE)
endif

PYTEST_ARGS=-c $(PYTEST_CFG) $(SALT_TESTS) $(PYTEST_FLAGS)
CMD=py.test $(PYTEST_ARGS)
EXEC=docker run $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) tests

ifndef RPDB_PORT
docker_shell : EXEC=docker run -it $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE)
else
docker_shell : EXEC=docker run -p $(RPDB_PORT):4444 -it $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE)
endif
docker_shell : CMD=/bin/bash
docker_shell :: pull_image
	$(EXEC)

saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/common.cfg
saltstack.unit : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=30
saltstack.unit : CMD:=timeout 30m $(CMD)
saltstack.unit :: pull_image
	$(EXEC)

saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/common.cfg
saltstack.integration : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=100
saltstack.integration : CMD:=timeout 40m $(CMD)
saltstack.integration :: pull_image
	$(EXEC)

suse.tests : PYTEST_CFG=./configs/suse.tests/$(VERSION)/$(FLAVOR).cfg
suse.tests : SALT_TESTS=./tests
suse.tests : EXEC=sandbox/bin/$(CMD)
ifneq ("$(FLAVOR)", "devel")
suse.tests : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=150
suse.tests : EXEC:=timeout 40m $(EXEC)
endif
suse.tests : pull_image
	$(EXEC)
