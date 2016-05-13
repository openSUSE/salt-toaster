import os
import pytest
from functools import partial
from fnmatch import fnmatch


def pytest_addoption(parser):
    parser.addini(
        "ignore_list",
        type="args",
        help="glob-style file patterns for Python test collect ignore",
        default=[]
    )
    parser.addini(
        "xfail_list",
        type="args",
        help="glob-style pytest node ids marked as expected failures",
        default=[]
    )


def pytest_ignore_collect(path, config):
    return any(map(path.fnmatch, config.getini('ignore_list')))


def pytest_itemcollected(item):
    matcher = partial(fnmatch, item.nodeid)
    if any(map(matcher, item.config.getini('xfail_list'))):
        item.addExpectedFailure(item.parent, None)


def pytest_configure(config):
    os.sys.path.extend([os.path.join(os.sys.path[0], 'tests')])


@pytest.fixture(scope="session")
def test_daemon(add_options, request):
    from integration import TestDaemon
    return TestDaemon(request.instance)


@pytest.fixture(scope="session")
def transplant_configs(test_daemon):
    test_daemon.transplant_configs(transport='zeromq')


@pytest.fixture(scope="session")
def add_options(request):
    from tests.runtests import SaltTestsuiteParser
    parser = SaltTestsuiteParser([])
    request.instance.options, args = parser.parse_args([])


@pytest.fixture(scope="session")
def salt_test_daemon(transplant_configs, test_daemon, request):
    finalizer = partial(test_daemon.__exit__, None, None, None)
    request.addfinalizer(finalizer)
    test_daemon.__enter__()
