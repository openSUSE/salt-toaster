import re
import pytest
import itertools
from saltcontainers.factories import ContainerFactory, MasterFactory


pytestmark = pytest.mark.xfail


MASTERS = [
   'registry.mgr.suse.de/toaster-sles15-products-next',
   'registry.mgr.suse.de/toaster-sles12sp3-products-next',
   'registry.mgr.suse.de/toaster-sles11sp4-products-old-testing',
]


CLIENTS = [
    'registry.mgr.suse.de/toaster-sles11sp4-products-old-testing',
    'registry.mgr.suse.de/toaster-sles12sp3-products-next',
    'registry.mgr.suse.de/toaster-sles15-products-next',
]


@pytest.fixture()
def client(request):
    obj = ContainerFactory(
        config__image=request.param,
        config__salt_config=None,
        ssh_config={'user': 'root', 'password': 'admin123'})
    request.addfinalizer(obj.remove)
    return obj


@pytest.fixture()
def master(request, salt_root, client):
    obj = MasterFactory(
        container__config__salt_config__tmpdir=salt_root,
        container__config__salt_config__conf_type='master',
        container__config__image=request.param,
        container__config__salt_config__extra_configs={
            "file_roots": {
                "file_roots": {"base": ["/etc/salt/sls"]}
            },
            "thin_extra_mods": {
                "thin_extra_mods": "msgpack"
            },
        },
        container__config__salt_config__sls=['tests/sls/echo.sls',],
        container__config__salt_config__roster=[client]
    )
    request.addfinalizer(obj['container'].remove)
    return obj


def pytest_generate_tests(metafunc):
    matrix = itertools.product(MASTERS, CLIENTS)
    def _ids(it):
        return re.match('registry.mgr.suse.de/toaster-(.+)', it).group(1).replace('-', '_')
    metafunc.parametrize(
        'master,client',
        matrix,
        ids=_ids,
        indirect=['master', 'client'])


def test_ping(master, client):
    assert master.salt_ssh(client, "test.ping") is True


def test_state_apply_log_file_created(master, client):
    res = master.salt_ssh(client, "state.apply echo")
    assert res['cmd_|-test_|-echo "test1"_|-run']['changes']['stdout'] == 'test1'
