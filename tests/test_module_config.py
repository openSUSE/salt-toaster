import os
import yaml
import py.path as path
from utils import upload
import pytest
import requests
from faker import Faker
from saltcontainers.factories import MasterFactory, ContainerFactory


PASSWORD = 'admin123'


@pytest.fixture(scope='module')
def bootstrap(request, docker_client, salt_root, module_config, controller, tmpdir_factory):
    config = dict(containers=[])
    for item in module_config.get('containers', []):
        config_item = dict(id=None, fixture=None)
        container = ContainerFactory(
            config__docker_client=docker_client,
            config__image=request.config.getini('BASE_IMAGE'),
            config__salt_config__tmpdir=salt_root,
            config__salt_config=None,
            config__volumes=None,
            config__host_config=None)
        container.run('cat docker/ssh/id_rsa.pub >> ~/.ssh/authorized_keys')
        container.run(
            'zypper ar -f http://nu.novell.com/SUSE/Products/SLE-SERVER/12-SP1/x86_64/product/ "SLES 12 SP1 Pool"')
        container.run(
            'zypper ar -f http://nu.novell.com/SUSE/Updates/SLE-SERVER/12-SP1/x86_64/update/ "SLES 12 SP1 Updates"')
        container.run('zypper -n in openssh python python-xml')
        container.run('ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N ""')
        container.run('ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -q -N ""')
        container.run('ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N ""')
        container.run('/usr/sbin/sshd')
        request.addfinalizer(container.remove)

        upload(
            container,
            (path.local(os.getcwd()) / 'docker' / 'ssh' / 'authorized_keys').strpath,
            '/root/.ssh/',
            tmpdir_factory)


        roster = (path.local(os.getcwd()) / 'tests' / 'roster')
        content = {
            container['config']['name']: {
                'user': 'root',
                'host': container['ip'],
                'priv': '/root/.ssh/id_rsa'
            }
        }
        roster.write(yaml.safe_dump(content, default_flow_style=False))
        upload(controller['container'], roster.strpath, '/etc/salt/', tmpdir_factory)

        import pdb; pdb.set_trace()
        response = requests.post(
            'http://{}:{}/hook/highstate?token={}'.format(
                controller['container']['ip'],
                controller['port'],
                controller['token']),
            headers={"Accept": "application/json"},
            json={
                'password': 'admin123',
                'target': container['config']['name'],
                'os': request.config.getini('TAGS')[1],
                'role': item['role']
            }
        )

        config['containers'].append(container)
    return config, module_config


@pytest.fixture(scope='module')
def module_config(request, controller):
    group = __name__
    return {'containers': [{'role': 'master'}, {'role': 'minion'}]}


@pytest.fixture(scope='session')
def controller(request, docker_client, salt_root, pillar_root, file_root, tmpdir_factory):
    fake = Faker()
    api_port = 8000
    controller = MasterFactory(
        container__config__docker_client=docker_client,
        container__config__name="controller_{}".format(fake.sha1()[:5]),
        container__config__image='registry.mgr.suse.de/toaster-sles12sp1-products',
        container__config__salt_config__tmpdir=salt_root,
        container__config__salt_config__config={
            'base_config': {
                'pillar_roots': {
                    'base': [pillar_root]
                },
                'file_roots': {
                    'base': [file_root]
                },
                "thin_extra_mods": "msgpack",
                "worker_threads": 1,
                "ssh_identities_only": True
            },
            "external_auth": {
                "external_auth": {
                    "auto": {
                        "saltuser": [
                            {"*": [
                                ".*",
                                "@wheel",
                                "@runner",
                                "@jobs"
                            ]}
                        ]
                    }
                }
            },
            "reactor": {
                "reactor": [
                    {'salt/netapi/hook/highstate': ['/etc/salt/sls/highstate.sls']}
                ]
            },
            "cherrypy": {
                "rest_cherrypy": {
                    "port": api_port,
                    "disable_ssl": True,
                    "webhook_disable_auth": True,
                    "webhook_url": "/hook"
                }
            }
        },
        container__config__salt_config__conf_type='master',
        container__config__salt_config__apply_states={
            "top": "tests/sls/module_config/top.sls",
            "setup": "tests/sls/module_config/setup.sls"})
    request.addfinalizer(controller['container'].remove)
    upload(
        controller['container'],
        (path.local(os.getcwd()) / 'tests/sls/module_config/').strpath,
        '/etc/salt/sls/',
        tmpdir_factory)
    upload(
        controller['container'],
        (path.local(os.getcwd()) / 'docker' / 'ssh').strpath,
        '/root/.ssh/',
        tmpdir_factory)

    # response = requests.post(
    #     'http://{}:{}/login'.format(
    #         controller['container']['ip'], api_port),
    #     headers={"Accept": "application/json"},
    #     json={'username': 'saltuser', 'password': 'saltuser', 'eauth': 'auto'}
    # )
    # response.raise_for_status()
    # controller['token'] = response.json()['return'][0]['token']
    controller['token'] = ''
    controller['port'] = api_port

    return controller


def test_provisioning(bootstrap):
    config, init_config = bootstrap
    import pdb; pdb.set_trace()
