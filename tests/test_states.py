import yaml
import time
import pytest
from faker import Faker


@pytest.fixture(scope="module")
def minion_id():
    fake = Faker()
    return u'{0}_{1}'.format(fake.word(), fake.word())


@pytest.fixture(scope="module")
def master_container_extras(minion_id):
    return dict(
        config__salt_config__id=minion_id,
        config__salt_config__sls={
            'latest': {'latest-state': {'pkg.latest': [{'name': 'postfix'}]}}
        }
    )


@pytest.fixture(scope="module")
def minion_container_extras(minion_id):
    return dict(config__salt_config__id=minion_id)


def test_pkg_latest_version(master, minion, minion_key_accepted):
    time.sleep(10)
    resp = master.salt(minion['id'], 'state.apply latest')
    assert resp[minion['id']]['pkg_|-latest-state_|-postfix_|-latest']['result']
