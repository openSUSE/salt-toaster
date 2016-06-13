import yaml
from docker import Client
import pytest


@pytest.fixture(scope="session")
def docker_client():
    client = Client(base_url='unix://var/run/docker.sock')
    return client


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="module")
def master_root(salt_root):
    return salt_root.mkdir("master")


@pytest.fixture(scope="module")
def minion_root(salt_root):
    return salt_root.mkdir("minion")


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def file_root(salt_root):
    return salt_root.mkdir('topfiles')
