DEFAULT_REGISTRY      = salttoaster
DEFAULT_VERSION       = opensuse151
DEFAULT_FLAVOR        = devel
SUSE_DEFAULT_REGISTRY = registry.mgr.suse.de
SUSE_DEFAULT_VERSION  = sles12sp3
SUSE_DEFAULT_FLAVOR   = products
TOASTER_MOUNTPOINT    = /salt-toaster
ROOT_MOUNTPOINT       = /salt/src
SALT_REPO_MOUNTPOINT  = $(ROOT_MOUNTPOINT)/salt-devel
SALT_TESTS            = $(ROOT_MOUNTPOINT)/salt-*/tests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(TOASTER_MOUNTPOINT)"
DESTRUCTIVE_TESTS     = False
EXPENSIVE_TESTS       = False

ifndef VERSION
	VERSION = $(DEFAULT_VERSION)
endif

ifneq (,$(findstring sles,$(FLAVOR)))
	FLAVOR = $(SUSE_DEFAULT_FLAVOR)
else ifneq (,$(findstring rhel,$(FLAVOR)))
	FLAVOR = $(SUSE_DEFAULT_FLAVOR)
else ifneq (,$(findstring ubuntu,$(FLAVOR)))
	FLAVOR = $(SUSE_DEFAULT_FLAVOR)
else ifndef FLAVOR
	FLAVOR = $(DEFAULT_FLAVOR)
endif

ifneq (,$(findstring sles,$(VERSION)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifneq (,$(findstring rhel,$(VERSION)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifneq (,$(findstring ubuntu,$(VERSION)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifndef DOCKER_REGISTRY
	DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
endif

ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
$(eval DOCKER_VOLUMES:=$(DOCKER_VOLUMES) -v $(SALT_REPO):$(SALT_REPO_MOUNTPOINT))
endif
endif

ifndef DOCKER_IMAGE
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(VERSION)-$(FLAVOR)
endif

ifdef DOCKER_MEM
	DOCKER_RES_LIMITS = --memory="$(DOCKER_MEM)"
endif

ifdef DOCKER_CPUS
	DOCKER_RES_LIMITS := $(DOCKER_RES_LIMITS) --cpus="$(DOCKER_CPUS)"
endif

EXPORTS += \
	-e "SALT_TESTS=$(SALT_TESTS)" \
	-e "VERSION=$(VERSION)" \
	-e "FLAVOR=$(FLAVOR)" \
	-e "DOCKER_IMAGE=$(DOCKER_IMAGE)" \
	-e "MINION_VERSION=$(MINION_VERSION)" \
	-e "MINION_FLAVOR=$(MINION_FLAVOR)" \
	-e "ROOT_MOUNTPOINT=$(ROOT_MOUNTPOINT)" \
	-e "SALT_REPO_MOUNTPOINT=$(SALT_REPO_MOUNTPOINT)" \
	-e "TOASTER_MOUNTPOINT=$(TOASTER_MOUNTPOINT)" \
	-e "DESTRUCTIVE_TESTS=$(DESTRUCTIVE_TESTS)" \
	-e "EXPENSIVE_TESTS=$(EXPENSIVE_TESTS)"

# Setting the defaults for a job execution in Jenkins
ifdef BUILD_ID
ifndef DOCKER_RES_LIMITS
	DOCKER_RES_LIMITS := --memory="2G" --cpus="1.5"
endif
endif

title:
	@echo
	@echo "███████╗ █████╗ ██╗  ████████╗    ████████╗ ██████╗  █████╗ ███████╗████████╗███████╗██████╗"
	@echo "██╔════╝██╔══██╗██║  ╚══██╔══╝    ╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗"
	@echo "███████╗███████║██║     ██║          ██║   ██║   ██║███████║███████╗   ██║   █████╗  ██████╔╝"
	@echo "╚════██║██╔══██║██║     ██║          ██║   ██║   ██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗"
	@echo "███████║██║  ██║███████╗██║          ██║   ╚██████╔╝██║  ██║███████║   ██║   ███████╗██║  ██║"
	@echo "╚══════╝╚═╝  ╚═╝╚══════╝╚═╝          ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝"
	@echo
	@echo "///////////////////////////////////////////////////"
	@echo "// Salt Toaster: An ultimate test suite for Salt //"
	@echo "//   https://github.com/openSUSE/salt-toaster/   //"
	@echo "///////////////////////////////////////////////////"
	@echo

help: title
	@echo "Commands:"
	@echo "  set_env                 Create environment"
	@echo "  list_targets            List available versions and flavors targets"
	@echo "  docker_shell            Start Docker shell"
	@echo "  saltstack.integration   Run Salt integration tests"
	@echo "  saltstack.unit          Run Salt unit tests"
	@echo "  suse.tests              Run SUSE custom integration tests"
	@echo ""

default: help

set_env:
	bin/prepare_environment.sh --create sandbox

list_targets: title
	@echo "Available public targets:"
	@echo "  OpenSUSE Leap 15.0      VERSION: opensuse150 - FLAVOR: devel"
	@echo "  OpenSUSE Leap 15.1      VERSION: opensuse151 - FLAVOR: devel"
	@echo "  OpenSUSE Tumbleweed     VERSION: tumbleweed  - FLAVOR: devel"
	@echo "  CentOS 7                VERSION: centos7     - FLAVOR: devel"
#	@echo "  Ubuntu 16.04            VERSION: ubuntu1604  - FLAVOR: devel"
#	@echo "  Ubuntu 18.04            VERSION: ubuntu1804  - FLAVOR: devel"
	@echo
	@echo "SUSE internal use only:"
	@echo "  SUSE SLE11SP4           VERSION: sles11sp4   - FLAVOR: products-old, products-old-testing, devel"
	@echo "  SUSE SLE12SP3           VERSION: sles12sp3   - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE12SP4           VERSION: sles12sp4   - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE15              VERSION: sles15      - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE15SP1           VERSION: sles15sp1   - FLAVOR: products, products-testing, products-next, devel"
	@echo "  RedHat RHEL6            VERSION: rhel6       - FLAVOR: products-old, products-old-testing, devel"
	@echo "  RedHat RHEL7            VERSION: rhel7       - FLAVOR: products, products-testing, products-next, devel"
	@echo "  Ubuntu 16.04            VERSION: ubuntu1604  - FLAVOR: products, products-testing, products-next, devel"
	@echo "  Ubuntu 18.04            VERSION: ubuntu1804  - FLAVOR: products, products-testing, products-next, devel"
	@echo

pull_image:
ifndef NOPULL
	docker pull $(DOCKER_IMAGE)
endif

# Temporary disable Docker containers MEM/CPU limitations
DOCKER_RES_LIMITS=

PYTEST_ARGS=-c $(PYTEST_CFG) $(SALT_TESTS) $(PYTEST_FLAGS)
CMD=pytest $(PYTEST_ARGS) --junitxml results.xml
EXEC=docker run $(EXPORTS) -t -e "CMD=$(CMD)" --label=$(ST_JOB_ID)  --rm $(DOCKER_VOLUMES) $(DOCKER_RES_LIMITS) $(DOCKER_IMAGE) tests

ifndef RPDB_PORT
docker_shell : EXEC=docker run -it $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_RES_LIMITS) $(DOCKER_IMAGE)
else
docker_shell : EXEC=docker run -p $(RPDB_PORT):4444 -it $(EXPORTS) -e "CMD=$(CMD)" --rm $(DOCKER_VOLUMES) $(DOCKER_RES_LIMITS) $(DOCKER_IMAGE)
endif
docker_shell : CMD=/bin/bash
docker_shell :: title pull_image
ifeq ("$(FLAVOR)", "devel")
ifndef SALT_REPO
	@echo "ERROR: Using 'devel' FLAVOR requires SALT_REPO";
	exit 1
endif
endif
	$(EXEC)

ifeq ("$(VERSION)", "sles15")
saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/sles15.cfg
else ifeq ("$(VERSION)", "sles11sp4")
saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/sles11sp4.cfg
else ifeq ("$(VERSION)", "rhel6")
saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/rhel6.cfg
else
saltstack.unit : PYTEST_CFG=./configs/saltstack.unit/common.cfg
endif
saltstack.unit : SALT_TESTS:=$(SALT_TESTS)/unit
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
saltstack.unit : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
saltstack.unit : CMD:=timeout 180m $(CMD)
endif
endif
saltstack.unit :: title pull_image
ifeq ("$(FLAVOR)", "devel")
ifndef SALT_REPO
	@echo "ERROR: Using 'devel' FLAVOR requires SALT_REPO"
	exit 1
endif
endif
	$(EXEC)

ifeq ("$(VERSION)", "sles15")
saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/sles15.cfg
else ifeq ("$(VERSION)", "sles11sp4")
saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/sles11sp4.cfg
else ifeq ("$(VERSION)", "rhel6")
saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/rhel6.cfg
else
saltstack.integration : PYTEST_CFG=./configs/saltstack.integration/common.cfg
endif
saltstack.integration : SALT_TESTS:=$(SALT_TESTS)/integration
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
saltstack.integration : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
saltstack.integration : CMD:=timeout 180m $(CMD)
endif
endif
saltstack.integration :: title pull_image
ifeq ("$(FLAVOR)", "devel")
ifndef SALT_REPO
	@echo "ERROR: Using 'devel' FLAVOR requires SALT_REPO"
	exit 1
endif
endif
	$(EXEC)

suse.tests : PYTEST_CFG=./configs/suse.tests/$(VERSION)/$(FLAVOR).cfg
suse.tests : SALT_TESTS=./tests
suse.tests : EXEC=sandbox/bin/$(CMD)
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
suse.tests : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
suse.tests : EXEC:=timeout 180m $(EXEC)
endif
endif

suse.tests : EXEC:=VERSION=$(VERSION) FLAVOR=$(FLAVOR) $(EXEC)
suse.tests : title pull_image
ifeq ("$(FLAVOR)", "devel")
ifndef SALT_REPO
	@echo "ERROR: Using 'devel' FLAVOR requires SALT_REPO"
	exit 1
endif
endif
	$(EXEC)
