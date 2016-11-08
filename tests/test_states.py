import yaml
import time
import pytest
from faker import Faker
from saltcontainers.factories import MinionFactory, MasterFactory


@pytest.fixture(scope='module')
def module_config(request, docker_client, salt_root, file_root, pillar_root):
    fake = Faker()

    master_name = 'master_{0}_{1}'.format(fake.word(), fake.word())
    master_image = request.config.getini('IMAGE')
    master_config = dict(
        container__config__name=master_name,
        container__config__docker_client=docker_client,
        container__config__image=master_image,
        container__config__salt_config__tmpdir=salt_root,
        container__config__salt_config__conf_type='master',
        container__config__salt_config__config={
            'base_config': {
                'pillar_roots': {'base': [pillar_root]},
                'file_roots': {'base': [file_root]}}},
        container__config__salt_config__sls={
            'latest': {'latest-state': {'pkg.latest': [{'name': 'postfix'}]}}})

    minion_name = 'minion_{0}_{1}'.format(fake.word(), fake.word())
    minion_image = master_image or request.config.getini('IMAGE')
    minion_config = dict(
        container__config__name=minion_name,
        container__config__docker_client=docker_client,
        container__config__image=minion_image,
        container__config__salt_config__tmpdir=salt_root,
        container__config__salt_config__conf_type='minion',
        container__config__salt_config__config={'base_config': {}})

    return {
        'masters': [
            {
                'config': master_config,
                'minions': [
                    {'config': minion_config}
                ]
            }
        ]
    }


def test_pkg_latest_version(setup):
    fixtures, config = setup
    master = fixtures[config['masters'][0]['id']]['fixture']
    minion = fixtures[master['id']]['minions'][0]
    resp = master.salt(minion['id'], 'state.apply latest')
    assert resp[minion['id']]['pkg_|-latest-state_|-postfix_|-latest']['result']
