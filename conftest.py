import pytest


@pytest.fixture(scope="session")
def transplant_configs():
    from integration import TestDaemon
    TestDaemon.transplant_configs(transport='zeromq')
