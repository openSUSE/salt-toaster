import pytest
from functools import partial


def pytest_generate_tests(metafunc):

    metafunc.parametrize(
        'test_container,component,should_be_installed',
        [
            # installed on master
            ['master', 'salt-minion', True],
            ['master', 'salt-proxy', True],
            ['master', 'salt', True],
            ['master', 'salt-master', True],
            ['master', 'salt-cp', True],
            ['master', 'salt-key', True],
            ['master', 'salt-run', True],
            ['master', 'spm', True],
            ['master', 'salt-call', True],
            ['master', 'salt-unity', True],

            # installed on minion
            ['minion', 'salt-minion', True],
            ['minion', 'salt-proxy', True],
            ['minion', 'salt', True],
            ['minion', 'salt-master', True],
            ['minion', 'salt-cp', True],
            ['minion', 'salt-key', True],
            ['minion', 'salt-run', True],
            ['minion', 'spm', True],
            ['minion', 'salt-call', True],
            ['minion', 'salt-unity', True],

            # not installed on master
            ['master', 'salt-api', False],
            ['master', 'salt-cloud', False],
            # salt-ssh is now installed in the docker image
            # needed in other tests
            # ['master', 'salt-ssh', False],
            ['master', 'salt-syndic', False],

            # not installed on minion
            ['minion', 'salt-api', False],
            ['minion', 'salt-cloud', False],
            # salt-ssh is now installed in the docker image
            # needed in other tests
            # ['minion', 'salt-ssh', False],
            ['minion', 'salt-syndic', False],
        ],
        ids=lambda it:
            ('installed' if it else 'not-installed') if isinstance(it, bool) else it,
        indirect=['test_container']
    )


@pytest.fixture()
def test_container(request):
    params = {
        'master': partial(request.getfixturevalue, 'master_container'),
        'minion': partial(request.getfixturevalue, 'minion_container')
    }
    return params[request.param]()


@pytest.mark.skiptags('devel')
def tests_component(test_container, component, should_be_installed):
    output = test_container.run([component, '--version'])
    if should_be_installed:
        assert 'executable file not found' not in str(output.decode())
    else:
        assert 'executable file not found' in str(output.decode())
