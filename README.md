[![Build Status](https://api.travis-ci.org/openSUSE/salt-toaster.svg?branch=master)](https://travis-ci.org/openSUSE/salt-toaster)

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

#### Run docker shell in repository image based on version and flavor
```bash
make docker_shell VERSION=sles12sp1 FLAVOR="testing"
```

#### Run docker shell in repository image based on version and bind rpdb port
```bash
make docker_shell VERSION=sles12sp1 RPDB_PORT="4444"
```


## For development


### Run a docker container on a specific image and install salt from a salt repository on host

```bash
DOCKER_IMAGE=toaster-sles12sp1 DEVEL=true SALT_REPO=/home/mdinca/repositories/salt/ make docker_shell
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
