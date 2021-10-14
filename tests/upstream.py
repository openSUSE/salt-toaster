import os
import pytest
import tarfile
import py.path
from faker import Faker
from saltcontainers.factories import ContainerFactory


def pytest_addoption(parser):
    parser.addoption('--salt-repo')


def upload(container, source, destination, tmpdir_factory):
    arch = tmpdir_factory.mktemp("archive") / 'arch.tar'
    with tarfile.open(arch.strpath, mode='w') as archive:
        for item in py.path.local(source).listdir():
            archive.add(
                item.strpath,
                arcname=item.strpath.replace(source, '.'))

    container.run('mkdir -p {0}'.format(destination))
    with arch.open('rb') as f:
        container['config']['docker_client'].put_archive(
            container['config']['name'], destination, f.read())


@pytest.fixture(scope="module")
def container(request, docker_client, tmpdir_factory):
    fake = Faker()
    obj = ContainerFactory(
        config__name='proxy_container_{0}_{1}_{2}'.format(fake.word(), fake.word(), os.environ.get('ST_JOB_ID', '')),  # pylint: disable=no-member
        config__docker_client=docker_client,
        config__image=request.config.getini('IMAGE'),
        config__environment={
            'ROOT_MOUNTPOINT': '/salt/src',
            'TOASTER_MOUNTPOINT': '/salt-toaster',
            'SALT_TESTS': '/salt/src/salt-2015.8.7/tests',
            'DISTRO': 'sles12sp1',
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
