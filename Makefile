DEFAULT_REGISTRY      = salttoaster
DEFAULT_DISTRO       = opensuse151
DEFAULT_FLAVOR        = devel
SUSE_DEFAULT_REGISTRY = registry.mgr.suse.de
SUSE_DEFAULT_VERSION  = sles12sp3
SUSE_DEFAULT_FLAVOR   = products
TOASTER_MOUNTPOINT    = /salt-toaster
ROOT_MOUNTPOINT       = /salt/src
SALT_REPO_MOUNTPOINT  = $(ROOT_MOUNTPOINT)/salt-devel
SALT_OLDTESTS         = tests
NO_NOX_SALT_TESTS     = $(ROOT_MOUNTPOINT)/salt-*/tests
SALT_PYTESTS          = tests/pytests
DOCKER_VOLUMES        = -v "$(CURDIR)/:$(TOASTER_MOUNTPOINT)"
DESTRUCTIVE_TESTS     = False
EXPENSIVE_TESTS       = False
NOX                   = True

ifndef ST_JOB_ID
	export ST_JOB_ID = local-test-run
endif

ifndef DISTRO
	DISTRO = $(DEFAULT_DISTRO)
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

ifneq (,$(findstring sles,$(DISTRO)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifneq (,$(findstring rhel,$(DISTRO)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifneq (,$(findstring ubuntu,$(DISTRO)))
	DOCKER_REGISTRY = $(SUSE_DEFAULT_REGISTRY)
else ifndef DOCKER_REGISTRY
	DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
endif

# Ubuntu devel images are stored on DockerHub
ifneq (,$(findstring ubuntu,$(DISTRO)))
ifneq (,$(findstring devel,$(FLAVOR)))
    DOCKER_REGISTRY = $(DEFAULT_REGISTRY)
endif
endif

ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
$(eval DOCKER_VOLUMES:=$(DOCKER_VOLUMES) -v $(SALT_REPO):$(SALT_REPO_MOUNTPOINT))
endif
endif

ifndef DOCKER_IMAGE
	DOCKER_IMAGE = $(DOCKER_REGISTRY)/toaster-$(DISTRO)-$(FLAVOR)
endif

ifdef DOCKER_MEM
	DOCKER_RES_LIMITS = --memory="$(DOCKER_MEM)"
endif

ifdef DOCKER_CPUS
	DOCKER_RES_LIMITS := $(DOCKER_RES_LIMITS) --cpus="$(DOCKER_CPUS)"
endif

ifeq ("$(FLAVOR)", "products-old")
NOX = False
else ifeq ("$(FLAVOR)", "products-old-testing")
NOX = False
else ifeq ("$(FLAVOR)", "products-3000")
NOX = False
else ifeq ("$(FLAVOR)", "products-3000-testing")
NOX = False
endif

ifndef DOCKER_FILE
	DOCKER_FILE = $(DISTRO).$(FLAVOR).dockerfile
endif

EXPORTS += \
	-e "SALT_OLDTESTS=$(SALT_OLDTESTS)" \
	-e "NO_NOX_SALT_TESTS=$(NO_NOX_SALT_TESTS)" \
	-e "SALT_PYTESTS=$(SALT_PYTESTS)" \
	-e "NOX=$(NOX)" \
	-e "DISTRO=$(DISTRO)" \
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
	DOCKER_RES_LIMITS := --memory="3G" --cpus="1.5"
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
	@echo "  build                   Build the docker images and set the entrypoint to one of the predefined ones."
	@echo "  build_image             Build the docker images and set the entrypoint to BASH."
	@echo "  archive-salt            Pack salt into a tarball and archive it"
	@echo ""

default: help

set_env:
	bin/prepare_environment.sh --create sandbox

list_targets: title
	@echo "Available public targets:"
	@echo "  openSUSE Leap 15.1      DISTRO: leap15.1     - FLAVOR: devel"
	@echo "  openSUSE Leap 15.2      DISTRO: leap15.2     - FLAVOR: devel"
	@echo "  openSUSE Leap 15.3      DISTRO: leap15.3     - FLAVOR: devel"
	@echo "  openSUSE Tumbleweed     DISTRO: tumbleweed   - FLAVOR: devel"
	@echo "  CentOS 7                DISTRO: centos7      - FLAVOR: devel"
	@echo "  Ubuntu 16.04            DISTRO: ubuntu16.04  - FLAVOR: devel"
	@echo "  Ubuntu 18.04            DISTRO: ubuntu18.04  - FLAVOR: devel"
	@echo
	@echo "SUSE internal use only:"
	@echo "  SUSE SLE11SP4           DISTRO: sles11sp4    - FLAVOR: products-old, products-old-testing, devel"
	@echo "  SUSE SLE12SP3           DISTRO: sles12sp3    - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE12SP4           DISTRO: sles12sp4    - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE15              DISTRO: sles15       - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE15SP1           DISTRO: sles15sp1    - FLAVOR: products, products-testing, products-next, devel"
	@echo "  SUSE SLE15SP2           DISTRO: sles15sp2    - FLAVOR: products-next, devel"
	@echo "  RedHat RHEL6            DISTRO: rhel6        - FLAVOR: products-old, products-old-testing, devel"
	@echo "  RedHat RHEL7            DISTRO: rhel7        - FLAVOR: products, products-testing, products-next, devel"
	@echo "  RedHat RHEL8            DISTRO: rhel8        - FLAVOR: products, products-testing, products-next, devel"
	@echo "  Ubuntu 16.04            DISTRO: ubuntu16.04  - FLAVOR: products, products-testing, products-next, devel"
	@echo "  Ubuntu 18.04            DISTRO: ubuntu18.04  - FLAVOR: products, products-testing, products-next, devel"
	@echo

pull_image:
ifndef NOPULL
	docker pull $(DOCKER_IMAGE)
endif

LEGACY_PYTEST_ARGS=-c $(PYTEST_CFG) $(NO_NOX_SALT_TESTS) $(PYTEST_FLAGS)
LEGACY_PYTEST_CMD=pytest $(LEGACY_PYTEST_ARGS) --junitxml results.xml

# New Toaster with pytest in nox
NOX_PYTEST_ARGS=-c $(PYTEST_CFG) $(SALT_OLDTESTS) $(SALT_PYTESTS) $(PYTEST_FLAGS)
GOTO_SALT_ROOT=cd $(ROOT_MOUNTPOINT)/salt-*
NOX_CMD=$(GOTO_SALT_ROOT) && mv ../conftest.py . && nox --session 'pytest-3(coverage=False)' -- $(NOX_PYTEST_ARGS) --junitxml results.xml

ifeq ("$(NOX)", "True")
CMD=$(NOX_CMD)
else
ifeq ("$(FLAVOR)", "devel")
CMD=PYTHONPATH=/salt/src/salt-devel/ $(LEGACY_PYTEST_CMD)
else
CMD=$(LEGACY_PYTEST_CMD)
endif
endif

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

ifeq ("$(DISTRO)", "sles11sp4")
saltstack.unit : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.unit/sles11sp4.cfg
else ifeq ("$(DISTRO)", "rhel6")
saltstack.unit : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.unit/rhel6.cfg
else
ifeq ("$(NOX)", "True")
saltstack.unit : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.unit/common.cfg
else
saltstack.unit : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.unit/common_legacy.cfg
endif
endif
saltstack.unit : SALT_OLDTESTS:=$(SALT_OLDTESTS)/unit
saltstack.unit : SALT_PYTESTS:=$(SALT_PYTESTS)/unit
saltstack.unit : NO_NOX_SALT_TESTS:=$(NO_NOX_SALT_TESTS)/unit
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
saltstack.unit : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
saltstack.unit : CMD:=timeout 180m sh -c \"$(CMD)\"
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

ifeq ("$(DISTRO)", "sles11sp4")
saltstack.integration : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.integration/sles11sp4.cfg
else ifeq ("$(DISTRO)", "rhel6")
saltstack.integration : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.integration/rhel6.cfg
else
ifeq ("$(NOX)", "True")
saltstack.integration : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.integration/common.cfg
else
saltstack.integration : PYTEST_CFG=$(TOASTER_MOUNTPOINT)/configs/saltstack.integration/common_legacy.cfg
endif
endif
saltstack.integration : SALT_OLDTESTS:=$(SALT_OLDTESTS)/integration
saltstack.integration : SALT_PYTESTS:=$(SALT_PYTESTS)/integration
saltstack.integration : NO_NOX_SALT_TESTS:=$(NO_NOX_SALT_TESTS)/integration
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
saltstack.integration : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
saltstack.integration : CMD:=timeout 180m sh -c \"$(CMD)\"
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

suse.tests : PYTEST_CFG=./configs/suse.tests/$(DISTRO)/$(FLAVOR).cfg
suse.tests : SALT_TESTS=./tests
suse.tests : PYTEST_ARGS=-c $(PYTEST_CFG) $(SALT_TESTS) $(PYTEST_FLAGS)
suse.tests : CMD=pytest $(PYTEST_ARGS) --junitxml results.xml
suse.tests : EXEC=sandbox/bin/$(CMD)
ifneq ("$(FLAVOR)", "devel")
ifdef JENKINS_HOME
suse.tests : PYTEST_ARGS:=$(PYTEST_ARGS) --timeout=500
suse.tests : EXEC:=timeout 180m $(EXEC)
endif
endif

suse.tests : EXEC:=DISTRO=$(DISTRO) FLAVOR=$(FLAVOR) $(EXEC)
suse.tests : title pull_image
ifeq ("$(FLAVOR)", "devel")
ifndef SALT_REPO
	@echo "ERROR: Using 'devel' FLAVOR requires SALT_REPO"
	exit 1
endif
endif
	$(EXEC)

archive-salt:
ifeq ("$(FLAVOR)", "devel")
ifdef SALT_REPO
	tar -X .tarexclude -czf images/docker/salt.archive -C $(SALT_REPO) .
endif
endif


build::
	@echo "Building images"
ifeq ("$(NOPULL)", "true")
	$(eval BUILD_OPTS:=--nopull)
endif

ifndef VENV
	DOCKER_IMAGE=$(DOCKER_IMAGE) DOCKER_FILE=$(DOCKER_FILE) python3 images/build.py $(BUILD_OPTS)
else
	DOCKER_IMAGE=$(DOCKER_IMAGE) DOCKER_FILE=$(DOCKER_FILE) $(VENV)/bin/python images/build.py $(BUILD_OPTS)
endif
	rm -f images/docker/salt.archive


build_image : CMD=""
build_image :: archive-salt build
	$(EXEC)

