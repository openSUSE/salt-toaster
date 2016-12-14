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
	-e "VERSION=$(VERSION)" \
	-e "FLAVOR=$(FLAVOR)" \
	-e "DOCKER_IMAGE=$(DOCKER_IMAGE)" \
	-e "DOCKER_FILE=$(DOCKER_FILE)" \
	-e "MINION_VERSION=$(MINION_VERSION)" \
	-e "MINION_FLAVOR=$(MINION_FLAVOR)" \
	-e "ROOT_MOUNTPOINT=$(ROOT_MOUNTPOINT)" \
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
	@echo "  build_image             Build Docker image"
	@echo "  saltstack.integration   Run Salt integration tests"
	@echo "  saltstack.unit          Run Salt unit tests"
	@echo "  suse.integration        Run SUSE custom integration tests"
	@echo ""

default: help

set_env:
	bin/prepare_environment.sh --create sandbox


archive-salt:
ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
	tar -X .tarexclude -czf docker/salt.archive -C $(SALT_REPO) .
else
	curl -s https://codeload.github.com/saltstack/salt/zip/develop > docker/develop.zip
	rm -f docker/salt.archive
	unzip docker/develop.zip -d docker > /dev/null
	rm -f docker/develop.zip
	tar -cvzf docker/salt.archive -C docker/salt-develop . > /dev/null
	rm -rf docker/salt-develop
endif
endif

build::
	@echo "Building images"
ifeq ("$(FLAVOR)", "devel")
	$(eval BUILD_OPTS:=--nopull)
endif
	DOCKER_IMAGE=$(DOCKER_IMAGE) DOCKER_FILE=$(DOCKER_FILE) sandbox/bin/python -m build $(BUILD_OPTS) > $(VERSION).$(FLAVOR).build.log || { \
	  cat $(VERSION).$(FLAVOR).build.log; \
	  exit 1; \
	}
	rm -f docker/salt.archive

pull_image:
ifndef NOPULL
	docker pull $(DOCKER_IMAGE)
endif

PYTEST_ARGS=-c $(PYTEST_CFG) $(SALT_TESTS) $(PYTEST_FLAGS)
CMD=py.test $(PYTEST_ARGS)
EXEC=docker run $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE) tests

build_image : CMD=""
build_image :: archive-salt build
	$(EXEC)

ifndef RPDB_PORT
docker_shell : EXEC=docker run -it $(EXPORTS) -e "CMD=/bin/bash" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE)
else
docker_shell : EXEC=docker run -p $(RPDB_PORT):4444 -it $(EXPORTS) -e "CMD=/bin/bash" --rm $(DOCKER_VOLUMES) $(DOCKER_IMAGE)
endif
docker_shell :: pull_image
	$(EXEC)

saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/common.cfg
saltstack.unit :: pull_image
	$(EXEC)

saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/common.cfg
saltstack.integration :: pull_image
	$(EXEC)

suse.tests : PYTEST_CFG=./configs/suse.tests/$(VERSION)/$(FLAVOR).cfg
suse.tests : SALT_TESTS=./tests
suse.tests : EXEC=sandbox/bin/$(CMD)
suse.tests : pull_image
	$(EXEC)
