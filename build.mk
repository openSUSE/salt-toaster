ifeq ($(BASE), sle12)
DIR = sles12
CONTAINER_NAME = toaster-sles12
else ifeq ($(BASE), sle12sp1)
DIR = sles12sp1
CONTAINER_NAME=toaster-sles12sp1
else ifeq ($(BASE), sle11sp3)
DIR = sles11sp3
CONTAINER_NAME=toaster-sles11sp3
else ifeq ($(BASE), sle11sp4)
DIR = sles11sp4
CONTAINER_NAME = toaster-sles11sp4
else
$(error Build command: BASE=sles11sp3 | sles11sp4 | sle12 | sles12sp1 make build)
endif

ROOT = $(CURDIR)/docker
DESTINATION = $(ROOT)/$(DIR)

build:
	@read -p "Enter the new container's version number: " VERSION; \
	DESTINATION=$(DESTINATION) \
	CONTAINER_NAME=$(CONTAINER_NAME) \
	VERSION=$$VERSION \
	$(ROOT)/generate_dockerfile.sh
	docker build -t $(CONTAINER_NAME) $(DESTINATION)
