# Salt Toaster: Advanced Documentation

## Ignore/Xfail upstream tests

From: [conftest_source_legacy.py#L12-L289](conftest_source_legacy.py) or
[conftest_source_nox.py#L12-L289](conftest_source_nox.py) 

```python
KNOWN_ISSUES_INTEGRATION = {
    'ignore_list': {
        'common': [
            'integration/files/file/base/*'  # <1>
        ],
        'products-next': [
            '*::MasterTest::test_exit_status_correct_usage'  # <2>
        ]

    },
    'xfail_list': {
        'products':[
            'integration/fileserver/roots_test.py::RootsTest::test_symlink_list'  # <3>
        ]
        'rhel6/products': [
            'integration/cli/grains.py::GrainsTargetingTest::test_grains_targeting_disconnected'  # <4>
        ]
    }
}
```

1. ignore all upstream integration tests found in `integration/files/file/base/` on all OS and salt-package version testsuite runs
1. ignore single test `MasterTest::test_exit_status_correct_usage` on runs using the `products-next` salt-package version
1. xfail single test `RootsTest::test_symlink_list` on runs using the `products` salt-package version
1. xfail single test `GrainsTargetingTest::test_grains_targeting_disconnected` on runs using `rhel6` OS and `products` salt-package version combination


### Tags

Tags can be used to identify the context in which a test runs.  
NOTE: tags are only used when running `suse.tests`

Tags are set in pytest configuration files in the https://github.com/openSUSE/salt-toaster/tree/master/configs[./configs] folder.

Running `VERSION=sles12sp1 FLAVOR=products make suse.tests` uses the following pytest config file:

Source: [`./configs/suse.tests/sles12sp2/products.cfg`](https://github.com/openSUSE/salt-toaster/blob/master/configs/suse.tests/sles12sp1/products.cfg)

```ini
[pytest]
addopts = --tb=short
IMAGE = registry.mgr.suse.de/toaster-sles12sp1-products
TAGS = sles sles12sp1 products
```

This means that a test can be xfailed on `sles12sp` like this:

```python
@pytest.mark.xfailtags('sles12sp1')
def test_example():
    pass
```

It can be skipped on all test runs using the `products` salt-package version like this:

```python
@pytest.mark.skiptags('products')
def test_example():
    pass
```

And it can be allowed to run only on `sles` like this:

```python
@pytest.mark.tags('sles')
def test_example():
    pass
```

In order for the `sles` tag to work as expected, it needs to be present in all config files used with sles: `./configs/suse.tests/sles*/*.cfg`
Likewise, the `products` tag would need to be present in all config files used with salt `products`: `./configs/<tests-type>/<os>/products.cfg`

Because tags are just identifiers you placed in the config files, you can create your own according to your needs. Just make sure you put them in the right config files.


### How to write a suse integration test

Writing a "test.ping" test

For this we need a salt master and a minion.
We can do that by creating a new file in the `tests` folder:

`./tests/test_example.py`

```python
def test_ping_minion(master, minion):
    pass
```

This uses `master` and `minion` fixtures defined in `tests/conftest.py`.

NOTE: The fixtures defined in `conftest.py` (or in the current file) are automatically discovered by `py.test`

The fixtures come from [pytest-salt-containers](https://pypi.python.org/pypi/pytest-salt-containers) plugin which uses
[factory-boy](https://pypi.python.org/pypi/factory_boy/) internally.
The factories take care of isolating the `sast-master` and `salt-minion` in separate containers.

With this, we have a running salt-master and a salt-minion.

To make master accept minion, I have created a convenient fixture called `minion_key_accepted`
Let's modify the test above to use it.

`./tests/test_example.py`
```python
def test_ping_minion(master, minion, minion_key_accepted):
     pass
```

To run `salt <minion-id> test.ping` on master and assert minion replied, do this:

`./tests/test_example.py`
```python
def test_ping_minion(master, minion, minion_key_accepted):
     assert master.salt(minion['id'], "test.ping")[minion['id']] is True
```

This might fail sometimes because the command might be run before .
In order to avoid that, I have created a `retry` helper that raises an exception if the command was not successful within `config.TIME_LIMIT`. So we need to change the test like this:

`./tests/test_example.py`

```python
from utils import retry


def test_ping_minion(master, minion, minion_key_accepted):

    def ping():
        return master.salt(minion['id'], "test.ping")[minion['id']]
        assert retry(ping)
```

Complex test requirements

When the requirements of the test are more complex, there's another way to define the containers in a single json.

Source: [`./tests/test_saltapi.py`](https://github.com/openSUSE/salt-toaster/blob/master/tests/test_saltapi.py#L4-L35)

```python
@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [  # <1>
            {
                "config": {  # <2>
                    'container__config__salt_config__sls': {  # <3>
                        'saltapi': 'tests/sls/saltapi.sls',
                    },
                    "container__config__salt_config__extra_configs": {  # <4>
                        "rosters_paths": {  # <5>
                            "rosters": ['/salt-toaster/tests/data/good.roster'],
                        },
                        "salt_api_config": {  # <6>
                            "rest_cherrypy": {
                                "port": 9080,
                                "host": "127.0.0.1",
                                "collect_stats": False,
                                "disable_ssl": True,
                            },
                            "external_auth": {  # <7>
                                "auto": {
                                    "admin": ['.*', '@wheel', '@runner', '@jobs']
                                },
                            },
                        },
                    },
                },
                "minions": [{"config": {}}]  # <8>
            }
        ]
}
```

1. a list of dictionaries. each item in the list will generate a container and run salt-master inside
1. configuration dictionary for the master
1. use ``container__config__salt_config__sls`` to specify an sls file that will be executed during the master set-up stage
1. use ``container__config__salt_config__extra_configs`` to create config files for salt in `/etc/salt/master.d` in the master container
1. this creates the file `/etc/salt/master.d/rosters_paths.conf` in the master container
1. this creates the file `/etc/salt/master.d/salt_api_config.conf` in the master container
1. this creates the file `/etc/salt/external_auth.conf` in the master container
1. define the minions that will be controlled by this master. the minions can be defined as dictionary in the same way masters are defined as described above.

### Running the test that we just wrote

The next thing after writing the test would probably be to run it.
We would do that with:

```
make suse.tests SALT_TESTS=tests/test_example.py::test_ping_minion`
```

This will run the test with the default `VERSION` and `FLAVOR` values but we probably wrote the test in order to implement a new salt feature or to fix some bug.
In this case we would probably want to run the test using the local checked out salt repository.
We do that with:

```
make suse.tests FLAVOR=devel SALT_REPO=/home/store/repositories/salt SALT_TESTS=tests/test_example.py::test_ping_minion
```

The test will probably fail (we didn't fix the issue yet). We can then change the salt source code and run the test again. The changes are immediatelly visible in the tests. We don't have to do anything extra, we just need to run the test again with the command above.

When running the tests with `FLAVOR=devel`, when changing beetween salt branches we might get:

```
AttributeError: 'module' object has no attribute 'BASE_THORIUM_ROOTS_DIR'
```

We can get over this by removing the `*.pyc` files from the salt repo using `find . -name "*.pyc" -delete`
