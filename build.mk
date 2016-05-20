ifeq ($(BASE), sle12)
SOURCE=$(CURDIR)/docker/sles12
CONTAINER_NAME=toaster-sles12
else ifeq ($(BASE), sle12sp1)
SOURCE=$(CURDIR)/docker/sles12sp1
CONTAINER_NAME=toaster-sles12sp1
else ifeq ($(BASE), sle11sp3)
SOURCE=$(CURDIR)/docker/sles11sp3
CONTAINER_NAME=toaster-sles11sp3
else ifeq ($(BASE), sle11sp4)
SOURCE=$(CURDIR)/docker/sles11sp4
CONTAINER_NAME=toaster-sles11sp4
else
$(error Build command: BASE=sles11sp3 | sles11sp4 | sle12 | sles12sp1 make build)
endif

build:
	docker build -t $(CONTAINER_NAME) $(SOURCE)
