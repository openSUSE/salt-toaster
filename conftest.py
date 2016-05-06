import pytest
from functools import partial
from fnmatch import fnmatch


def pytest_ignore_collect(path, config):
    ignore_list = [
        # ImportError: No module named integration
        'integration/fileclient_test.py',
        'integration/cli/batch.py',
        'integration/cli/custom_module.py',
        'integration/cli/grains.py',
        'integration/utils/test_reactor.py',
        'integration/renderers/pydsl_test.py',
        # NameError: global name 'azure' is not defined
        'integration/cloud/providers/msazure.py',
        'integration/files/file/base/*',
        # OSError: [Errno 2] No such file or directory
        'integration/modules/git.py',
    ]

    return any(map(path.fnmatch, ignore_list))


def pytest_itemcollected(item):
    xfail_list = [
        'integration/states/git.py::GitTest::test_latest',
        'integration/states/git.py::GitTest::test_latest_empty_dir',
        'integration/states/git.py::GitTest::test_latest_failure',
        'integration/states/git.py::GitTest::test_latest_unless_no_cwd_issue_6800',
        'integration/states/git.py::GitTest::test_latest_with_rev_and_submodules',
        'integration/states/git.py::GitTest::test_numeric_rev',
        'integration/states/git.py::GitTest::test_present',
        'integration/states/git.py::GitTest::test_present_empty_dir',
        'integration/states/git.py::GitTest::test_present_failure',
        'integration/shell/key.py::KeyTest::test_keys_generation_no_configdir',
        'integration/shell/call.py::CallTest::test_issue_2731_masterless'
    ]
    matcher = partial(fnmatch, item.nodeid)
    if any(map(matcher, xfail_list)):
        item.addExpectedFailure(item.parent, None)


@pytest.fixture(scope="session")
def test_daemon(request):
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
def salt_test_daemon(add_options, transplant_configs, test_daemon, request):
    finalizer = partial(test_daemon.__exit__, None, None, None)
    request.addfinalizer(finalizer)
    test_daemon.__enter__()
