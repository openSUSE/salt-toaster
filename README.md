[![Build Status](https://api.travis-ci.org/openSUSE/salt-toaster.svg?branch=master)](https://travis-ci.org/openSUSE/salt-toaster)

# salt-toaster

## Setup
```bash
virtualenv sandbox
. sandbox/bin/activate
pip install -r requirements.txt
```

## Running tests

### Run tests in default docker image:
```bash
git clone https://github.com/dincamihai/salt-toaster.git
cd salt-toaster
VERSION=sles12sp1 FLAVOR=devel SALT_REPO=/home/store/repositories/salt make -s suse.tests SALT_TESTS="tests/test_pkg.py"
VERSION=sles12sp1 FLAVOR=devel SALT_REPO=/home/store/repositories/salt make saltstack.unit SALT_TESTS=/salt/src/salt-devel/tests/unit/modules/zypper_test.py
```

### Examples

#### Run docker shell in specific local image
```bash
VERSION=sles12sp1 FLAVOR=products make docker_shell
```

#### Run docker shell in repository image based on version and bind rpdb port
```bash
RPDB_PORT="4444" VERSION=sles12sp1 FLAVOR=products make docker_shell
```

#### Run suse tests
- run a specific suse test
```bash
VERSION=sles12sp1 FLAVOR=products make -s suse.tests SALT_TESTS="tests/test_pkg.py::test_pkg_info_available"
```
- run all suse tests using salt installed from a localy repository
```bash
VERSION=sles12sp1 FLAVOR=devel SALT_REPO=/home/store/repositories/salt make -s suse.tests
```

#### Run upstream tests
- run a subset of upstream unit tests
```bash
VERSION=sles12sp1 FLAVOR=products make saltstack.unit SALT_TESTS=/salt/src/salt-devel/tests/unit/modules/zypper_test.py
```
- run all upstream integration tests
```bash
VERSION=sles12sp1 FLAVOR=products make saltstack.integration
```

## For development


### Run a docker container on a specific image and install salt from a salt repository on host

```bash
VERSION=sles12sp1 FLAVOR=devel SALT_REPO=/home/store/repositories/salt make docker_shell
```


### How to write tests and how they work

#### Writing a "test.ping" test

For this we need a salt master and a minion.
We can do that by creating a new file in the `tests` folder:

> ./tests/test_example.py
> ```python
> def test_ping_minion(master, minion):
>     pass
> ```

This uses `master` and `minion` fixtures defined in `tests/conftest.py`.

_Note: The fixtures defined in `conftest.py` (or in the current file) are automatically discovered by `py.test`_

The fixtures rely on [fatory-boy](https://pypi.python.org/pypi/factory_boy/) factories defined in `tests/factories.py`.
The factories take care of running `sast-master` and `salt-minion` in separate docker containers (it is also possible to run them in the same container).

With this, we have a running salt-master and a salt-minion.

To make master accept minion, I have created a convenient fixture called `minion_key_accepted`
Let's modify the test above to use it.

> ./tests/test_example.py
> ```python
> def test_ping_minion(master, minion, minion_key_accepted):
>      pass
> ```

To run `salt <minion-id> test.ping` on master and assert minion replied, do this:

> ./tests/test_example.py
> ```python
> def test_ping_minion(master, minion, minion_key_accepted):
>      assert master.salt(minion['id'], "test.ping")[minion['id']] is True
> ```

This might fail sometimes because the command might be run before .
In order to avoid that, I have created a `retry` helper that raises an exception if the command was not successful within `config.TIME_LIMIT`. So we need to change the test like this:

> ./tests/test_example.py
> ```python
> from utils import retry
>
>
> def test_ping_minion(master, minion, minion_key_accepted):
> 
>     def ping():                                                                 
>         return master.salt(minion['id'], "test.ping")[minion['id']]             
>                                                                                
>     assert retry(ping)       
> ```
