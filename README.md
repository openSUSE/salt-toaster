# Salt Toaster: An ultimate test suite for Salt

[![Building Docker Images](https://github.com/openSUSE/salt-toaster/actions/workflows/build-images.yml/badge.svg?branch=master)](https://github.com/openSUSE/salt-toaster/actions/workflows/build-images.yml)

## Description

This is a tool used to test https://github.com/saltstack/salt/[salt]

It uses pytest and containers to do so.

The tests are separated in 3 groups:

 - Saltstack upstream integration tests
 - Saltstack upstream unit tests
 - SUSE custom integration tests

When running the upstream tests, a docker container is created first and then `py.test` is being run inside the
container.

For the suse tests, the approach is different. `py.test` is being run on the host and the containers are created and
used as objects in the tests.

There are predefined flavors of salt packages plus a `devel` flavor.
The predefined flavors are packages served from OBS, see the (incomplete) list below:

 - [products](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products/salt)
 - [products:testing](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:testing/salt)
 - [products:next](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:next/salt)
 - [products:next:testing](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:next:testing/salt)

The `devel` flavor means that you can mount your host salt repository to `container:/salt/src/salt-devel` and then
install it inside the container. This allows testing Salt from a local repository.

Example (run in `salt-toaster` folder):

``` sh
make docker_shell DISTRO=sles15sp2 FLAVOR=devel SALT_REPO=/home/store/repositories/salt
```

## Features

 - Uses containers to isolate the tests
 - Possible to run the tests on different operating systems
 - Possible to run the tests in any available (OS, salt-package-version) combination
 - Capable to run the tests using salt from a local git repository
 - Capable of running a subset of tests
 - Has ignore and xfail lists (glob-patterns) for the upstream tests (for both integration and unit tests)
 - Uses tags to restrict, skip, ignore or xfail suse tests

## How to run Salt Toaster

The setup is pretty typical for small Python projects. Just clone the
repository, create a virtual environment, activate it and install the dependencies.

### Prerequisites:

openSUSE system with Python3:

```bash
sudo zypper in docker python3 make
```

Debian system: Your systems need to have docker and docker.io pkg installed

```bash
sudo apt install docker.io || sudo apt install docker
```

If you are part of the SUSE R&D network, you can access the non-public images. Please read the instructions here
[SUSE internal only](README_SUSE.md).

### Preparing the sandbox:

```bash
git clone https://github.com/openSUSE/salt-toaster.git
cd salt-toaster
python3 -m venv sandbox
. sandbox/bin/activate
pip install -r requirements.txt
```

If you choose a different name for your virtual environment, you need to specify
it later as `VENV` when you use `make`.

## Generate docker files

### Generate all files

The following will generate all flavors for all distros.

``` sh
python generate.py --all
```

### Generate for one or more specific distro(s)

The following will generate *all flavors* for *all specified* distros.

``` sh
python generate.py --distro sle15 
# these aliases also work
python generate.py --distros sle15 sle15sp2
python generate.py -d sle15
```

### Generate for one or more specific flavor(s)

The following will generate the *specified flavors* for *all distros*. 

``` sh
python generate.py --flavor products 
# these aliases also work
python generate.py --flavors products products-testing
python generate.py -f products
```

### Generate for one or more specific flavor-distro combination

The following will generate each *specified flavor* for each *specified distro*.

``` sh
python generate.py --flavor products products-testing --distros sle15 sle15sp2
```

### Generate for one or more specific distro and flavor=devel

The devel flavor uses `BASE_FLAVOR` to install dependencies.

``` sh
BASE_FLAVOR=products-testing python generate.py --distro sles15 --flavor devel
```

## Building New Images

### Docker Build

`make` is used to invoke a Python script that triggers the "`docker build`".

``` sh
make build_image DISTRO=sles15sp2 FLAVOR=products
```

If you named your virtual environment something other than `sandbox`, you can
pass it to `make` using `VENV`.

``` sh
make build_image DISTRO=sles15sp2 FLAVOR=products VENV=venv
```

Devel images require a `SALT_REPO` parameter.

``` sh
make build_image DISTRO=sles15sp2 FLAVOR=devel SALT_REPO=/path/to/local/salt/repo
```

### Show help:

```bash
make help
```

### List available targets:

In order to list the what targets (DISTRO and FLAVOR) are available for testing:

```bash
make list_targets
```

### Running the tests

When running tests we can choose to run:

    - Saltstack upstream integration testsuite `make saltstack.integration`
    - Saltstack upstream unit testsuite `make saltstack.unit`
    - SUSE custom testsuite `make suse.tests`

When running any of these commands, salt-toaster uses the default values for OS and salt-package version.

At the moment, the default DISTRO is `leap15.1` and FLAVOR is `devel`

The first step this command will perform is to pull the right container image from the respective Docker registry.

### Parameters

#### DISTRO

Most of the time we want to run the tests against a specific OS.
We can do so by using the `DISTRO` environmental variable.

```
make suse.tests DISTRO=leap15.1
```

#### FLAVOR

The salt flavor can be specified using the `FLAVOR` environmental variable.

```
make suse.tests FLAVOR=products-testing
```

Of course, `DISTRO` and `FLAVOR` can be combined

```
make suse.tests DISTRO=sles15 FLAVOR=products-testing
```

#### SALT_REPO

To run the tests against a local salt repository, you need to use `FLAVOR=devel` and you also need to specify the path
to the salt repository with `SALT_REPO`

```
make suse.tests FLAVOR=devel SALT_REPO=/home/store/repositories/salt
```

#### SALT_TESTS

You can specify a subset of tests to run using `SALT_TESTS`

```
make suse.tests SALT_TESTS=tests/test_pkg.py
make saltstack.unit SALT_TESTS=/salt/src/salt-*/tests/unit/modules/zypper_test.py
```

#### PYTEST_FLAGS
You can pass extra py.test parameters using `PYTEST_FLAGS`

```
make suse.tests SALT_TESTS=tests/test_pkg.py PYTEST_FLAGS=-x
```

#### DESTRUCTIVE_TESTS

Salt tests marked as "destructive" tests are currently disabled by default. If you want to run then, simple set
`DESTRUCTIVE_TESTS=True`

```
make saltstack.integration DESTRUCTIVE_TESTS=True
```

#### EXPENSIVE_TESTS

Salt tests marked as "expensive" tests are currently disabled by default. If you want to run then, simple set
`EXPENSIVE_TESTS=True`

```
make saltstack.integration EXPENSIVE_TESTS=True
```

When running the `suse.tests`, `SALT_TESTS` must be a path relative to the current folder (salt-toaster)

When running the `saltstack.unit` or `saltstack.integration`, `SALT_TESTS` must be a path inside the docker container
pointing to where the salt source code is extracted. Using a pattern like in the example above should always match
independent of the salt-package version.

Available public targets (`DISTRO` and `FLAVOR`):

| Name | Variable |
| ---- | -------- |
| DISTRO | leap15.1, leap15.2, tumbleweed, centos7, ubuntu1604, ubuntu1804 |
| FLAVOR | devel |


Available SUSE private (R&D network only) targets (`DISTRO` and `FLAVOR`):

| Name   | Variable |
| ------ | -------- |
| DISTRO | rhel6, rhel7, sles11sp3, sles11sp4, sles12, sles12sp1, sles12sp3, sles15, sles15sp1|
| FLAVOR | products, products-testing, products-next, devel |

#### DOCKER_CPUS and DOCKER_MEM

With these two parameters you can limit the resouce usage of the spun up Docker container. Examples would be `2G` or
`512M` for `DOCKER_MEM` and `1` or `2.5` for `DOCKER_CPUS`. Where the number provided for `DOCKER_CPUS` would the number
of host CPUs the container should able to use.

Please take a look at the official
[Docker documentation](https://docs.docker.com/config/containers/resource_constraints/) for more information about
[DOCKER_MEM](https://docs.docker.com/config/containers/resource_constraints/#limit-a-containers-access-to-memory) and
[DOCKER_CPUS](https://docs.docker.com/config/containers/resource_constraints/#cpu).

## Examples

Run docker shell in specific local image

```
make docker_shell DISTRO=sles15sp3 FLAVOR=products
```

Run docker shell in repository image based on version and bind rpdb port

```
make docker_shell RPDB_PORT="4444" DISTRO=sles15sp3 FLAVOR=products
```

Run a specific suse test using a local salt repository and sles12sp1

```
make -s suse.tests DISTRO=sles15sp3 FLAVOR=devel SALT_TESTS="tests/test_pkg.py::test_pkg_info_available"
```

Run a subset of upstream unit tests

```
make saltstack.unit DISTRO=sles15sp3 FLAVOR=products SALT_TESTS=/salt/src/salt-*/tests/unit/modules/zypper_test.py
```

Run all upstream integration tests

```
make saltstack.integration DISTRO=sles15sp3 FLAVOR=products
```

## Advanced Usage:

Please read the [Advanced README](README_ADVANCED.md) file.

## Demo:

[![asciicast](https://asciinema.org/a/254109.svg)](https://asciinema.org/a/254109)
