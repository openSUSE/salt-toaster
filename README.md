# salt-toaster


## Running tests

### Run tests in default docker image:
```bash
git clone https://github.com/dincamihai/salt-toaster.git
cd salt-toaster
make docker_run_custom_integration_tests
make docker_run_salt_integration_tests
make docker_run_salt_unit_tests
```

### Examples

#### Run docker shell in specific local image
```bash
make docker_shell DOCKER_IMAGE=toaster-sles12sp1
```

#### Run docker shell in specific repository image
```bash
make docker_shell DOCKER_IMAGE=registry.mgr.suse.de/toaster-sles12sp1
```

#### Run docker shell in repository image based on version
```bash
make docker_shell VERSION=sles12sp1
```


## Building containers

```bash
BASE=sle12sp1 make -f Makefile.build build
Enter the new container's version number: 1.0.1
```
This would rebuild **toaster-sles12sp1** but you still have to tag and push accordingly.


## For development


### Run a docker container on a specific image and install salt from a salt repository on host

```bash
DOCKER_IMAGE=toaster-sles12sp1 DEVEL=true SALT_REPO=/home/mdinca/repositories/salt/ make docker_shell
```
