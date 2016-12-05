import pytest
import tarfile
import py.path
from saltcontainers.factories import ContainerFactory
from utils import upload


def pytest_addoption(parser):
    parser.addoption('--salt-repo')


@pytest.fixture(scope="module")
def container(request, docker_client, tmpdir_factory):
    obj = ContainerFactory(
        config__docker_client=docker_client,
        config__image=request.config.getini('IMAGE'),
        config__environment={
            'ROOT_MOUNTPOINT': '/salt/src',
            'TOASTER_MOUNTPOINT': '/salt-toaster',
            'SALT_TESTS': '/salt/src/salt-2015.8.7/tests',
            'VERSION': 'sles12sp1',
        },
        config__salt_config=None,
        config__host_config=None
    )
    upload(obj, request.config.rootdir.parts()[-2].strpath, '/salt-toaster', tmpdir_factory)
    request.addfinalizer(obj.remove)
    return obj


def test_unit(container):
    stream = container.run(
        'make -f /root/Makefile -C /salt-toaster run_salt_unit_tests',
        stream=True)
    for item in stream:
        print(item),


def test_integration(container):
    stream = container.run(
        'make -f /root/Makefile -C /salt-toaster run_salt_integration_tests',
        stream=True)
    for item in stream:
        print(item),
