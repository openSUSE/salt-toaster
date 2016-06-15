import os
import re
import json
import yaml
import string
import factory
import factory.fuzzy
from docker import Client


class BaseFactory(factory.Factory):

    class Meta:
        strategy = factory.BUILD_STRATEGY


class ImageFactory(factory.StubFactory):
    tag = 'registry.mgr.suse.de/toaster-sles12sp1'
    docker_client = factory.LazyAttribute(
        lambda o: o.factory_parent.factory_parent.docker_client)

    @classmethod
    def stub(cls, **kwargs):
        obj = super(ImageFactory, cls).stub(**kwargs)
        output = obj.docker_client.build(
            os.getcwd() + '/tests2/docker/sles12sp1/',
            tag=obj.tag,
            pull=True,
            decode=True,
            # nocache=True
        )
        for item in output:
            print item.values()[0]
        return obj


class DockerClientFactory(factory.StubFactory):

    @classmethod
    def stub(cls, **kwargs):
        return Client(base_url='unix://var/run/docker.sock')


class SaltConfigFactory(BaseFactory):

    tmpdir = None
    root = factory.LazyAttribute(lambda o: o.tmpdir.mkdir(o.factory_parent.name))
    conf_type = None
    config = {}
    pillar = {}
    docker_client = None
    id = None

    class Meta:
        model = dict

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        assert kwargs['id']
        obj['id'] = kwargs['id']
        config_file = obj['root'] / obj['conf_type']
        main_config = {
            'include': '{0}.d/*'.format(obj['conf_type'])
        }
        if obj['conf_type'] in ['minion', 'proxy']:
            main_config['id'] = obj['id']

        config_file.write(
            yaml.safe_dump(main_config, default_flow_style=False))

        config_path = obj['root'].mkdir('{0}.d'.format(obj['conf_type']))
        for name, config in obj['config'].items():
            config_file = config_path / '{0}.conf'.format(name)
            config_file.write(yaml.safe_dump(config, default_flow_style=False))

        pillar_path = obj['root'].mkdir('pillar')
        for name, content in obj['pillar'].items():
            sls_file = pillar_path / '{0}.sls'.format(name)
            sls_file.write(yaml.safe_dump(content, default_flow_style=False))


class ContainerConfigFactory(BaseFactory):
    name = factory.fuzzy.FuzzyText(
        length=5, prefix='container_', chars=string.ascii_letters)
    salt_config = factory.SubFactory(SaltConfigFactory)
    image_obj = factory.SubFactory(ImageFactory)
    image = factory.SelfAttribute('image_obj.tag')
    command = '/bin/bash'
    tty = True
    stdin_open = True
    working_dir = "/salt-toaster/"
    ports = [4000, 4506]
    volumes = factory.LazyAttribute(
        lambda obj: [obj.salt_config['root'].strpath, os.getcwd()]
    )
    host_config = factory.LazyAttribute(
        lambda obj: obj.factory_parent.docker_client.create_host_config(
            port_bindings={},
            binds={
                obj.salt_config['root'].strpath: {
                    'bind': '/etc/salt/',
                    'mode': 'rw',
                },
                os.getcwd(): {
                    'bind': "/salt-toaster/",
                    'mode': 'rw'
                }
            }
        )
    )

    class Meta:
        model = dict
        exclude = ['image_obj', 'salt_config']


class ContainerModel(dict):

    def run(self, command):
        cmd_exec = self['docker_client'].exec_create(
            self['config']['name'], cmd=command)
        output = self['docker_client'].exec_start(cmd_exec['Id'])
        return output

    def get_suse_release(self):
        info = dict()
        content = self.run('cat /etc/SuSE-release')
        for line in content.split('\n'):
            match = re.match('([a-zA-Z]+)\s*=\s*(\d+)', line)
            if match:
                info.update([[match.group(1), int(match.group(2))]])
        return info

    def get_os_release(self):
        content = self.run('cat /etc/os-release')
        return dict(
            filter(
                lambda it: len(it) == 2,
                [it.replace('"', '').strip().split('=') for it in content.split('\n')]
            )
        )


class ContainerFactory(BaseFactory):

    docker_client = None
    config = factory.SubFactory(ContainerConfigFactory)
    ip = None

    class Meta:
        model = ContainerModel

    @classmethod
    def build(cls, **kwargs):
        obj = super(ContainerFactory, cls).build(**kwargs)
        obj['docker_client'].create_container(**obj['config'])
        obj['docker_client'].start(obj['config']['name'])
        data = obj['docker_client'].inspect_container(obj['config']['name'])
        obj['ip'] = data['NetworkSettings']['IPAddress']
        return obj


class MasterModel(dict):

    def salt_key_raw(self, *args):
        command = ['salt-key']
        command.extend(args)
        command.append('--output=json')
        return self['container'].run(' '.join(command))

    def salt_key(self, *args):
        return json.loads(self.salt_key_raw(*args))

    def salt_key_accept(self, minion_id):
        return self.salt_key_raw('-a', minion_id, '-y')

    def salt(self, minion_id, salt_command, *args):
        docker_command = "salt {0} {1} --output=json -l quiet".format(
            minion_id, salt_command, ' '.join(args))
        return json.loads(self['container'].run(docker_command))


class MasterFactory(BaseFactory):
    container = factory.SubFactory(
        ContainerFactory,
        config__name=factory.fuzzy.FuzzyText(
            length=5, prefix='master_', chars=string.ascii_letters)
    )

    class Meta:
        model = MasterModel

    @classmethod
    def build(cls, **kwargs):
        obj = super(MasterFactory, cls).build(**kwargs)
        docker_client = obj['container']['docker_client']
        res = docker_client.exec_create(
            obj['container']['config']['name'],
            cmd='salt-master -d -l debug'
        )
        docker_client.exec_start(res['Id'])
        return obj


class MinionModel(dict):

    def salt_call(self, salt_command, *args):
        docker_command = "salt-call {0} {1} --output=json -l quiet".format(
            salt_command, ' '.join(args)
        )
        return json.loads(self['container'].run(docker_command))['local']


class MinionFactory(BaseFactory):
    container = factory.SubFactory(
        ContainerFactory,
        config__name=factory.fuzzy.FuzzyText(
            length=5, prefix='minion_', chars=string.ascii_letters)
    )
    cmd = 'salt-minion -d -l debug'

    class Meta:
        model = MinionModel

    @classmethod
    def build(cls, **kwargs):
        obj = super(MinionFactory, cls).build(**kwargs)
        docker_client = obj['container']['docker_client']
        res = docker_client.exec_create(
            obj['container']['config']['name'], obj['cmd']
        )
        output = docker_client.exec_start(res['Id'])
        assert 'executable file not found' not in output
        return obj
