import pytest


def pytest_ignore_collect(path, config):
    ignore_list = [
        'integration/fileclient_test.py',
        'integration/cli/batch.py',
        'integration/cli/custom_module.py',
        'integration/cli/grains.py',
        'integration/cloud/providers/msazure.py',
        'integration/files/file/base/*',
        'integration/modules/git.py',
        'integration/client/*',
        'integration/wheel/*'
    ]
    return any(map(path.fnmatch, ignore_list))


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
def salt_test_deamon(add_options, transplant_configs, test_daemon, request):
    request.addfinalizer(test_daemon.__exit__)
    test_daemon.__enter__()
