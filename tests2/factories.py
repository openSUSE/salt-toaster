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


class SaltConfigFactory(BaseFactory):
    tmpdir = None
    root = factory.LazyAttribute(lambda o: o.tmpdir.mkdir(o.factory_parent.name))
    extraconf = None
    topfiles = None
    pillar = None
    conf_type = None
    id = None

    class Params:
        master = factory.Trait(
            extraconf=factory.LazyAttribute(lambda o: o.root.mkdir('master.d')),
            topfiles=factory.LazyAttribute(lambda o: o.root.mkdir('topfiles')),
            pillar=factory.LazyAttribute(lambda o: o.root.mkdir('pillar')),
            conf_type='master'
        )
        minion = factory.Trait(
            extraconf=factory.LazyAttribute(lambda o: o.root.mkdir('minion.d')),
            conf_type='minion',
            id=factory.SelfAttribute('..name')
        )
        proxy = factory.Trait(
            extraconf=factory.LazyAttribute(lambda o: o.root.mkdir('proxy.d')),
            conf_type='proxy',
            id=factory.SelfAttribute('..name')
        )

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        config_file = obj['root'] / obj['conf_type']
        base_config = {
            'include': '{0}.d/*'.format(obj['conf_type'])
        }
        if obj['conf_type'] in ['minion', 'proxy']:
            base_config['id'] = obj['id']

        config_file.write(
            yaml.safe_dump(base_config, default_flow_style=False))

        for name, config in kwargs.get('config', {}).items():
            config_file = obj['extraconf'] / '{0}.conf'.format(name)
            config_file.write(yaml.safe_dump(config, default_flow_style=False))

        for name, content in kwargs.get('pillar', {}).items():
            sls_file = obj['pillar'] / '{0}.sls'.format(name)
            sls_file.write(yaml.safe_dump(content, default_flow_style=False))

    class Meta:
        model = dict


class DockerClientFactory(factory.StubFactory):

    @classmethod
    def stub(cls, **kwargs):
        return Client(base_url='unix://var/run/docker.sock')


class HostConfigFactory(factory.StubFactory):
    docker_client = factory.LazyAttribute(
        lambda o: o.factory_parent.factory_parent.docker_client)
    salt_config = factory.SubFactory(SaltConfigFactory)

    @classmethod
    def stub(cls, **kwargs):
        obj = super(HostConfigFactory, cls).stub(**kwargs)
        return obj.docker_client.create_host_config(
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


class ContainerConfigFactory(BaseFactory):
    salt_config = factory.SubFactory(SaltConfigFactory)
    name = factory.fuzzy.FuzzyText(
        length=5, prefix='container_', chars=string.ascii_letters)
    image_obj = factory.SubFactory(ImageFactory)
    image = factory.SelfAttribute('image_obj.tag')
    command = '/bin/bash'
    tty = True
    stdin_open = True
    working_dir = "/salt-toaster/"
    ports = [4000, 4506]
    volumes = factory.LazyAttribute(
        lambda o: [
            o.salt_config['root'].strpath,
            "/home/mdinca/repositories/salt-toaster/"
        ]
    )
    host_config = factory.SubFactory(
        HostConfigFactory, salt_config=factory.SelfAttribute('..salt_config')
    )

    class Meta:
        model = dict
        exclude = ['salt_config', 'image_obj']


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
    id = factory.fuzzy.FuzzyText(
        length=5, prefix='minion_', chars=string.ascii_letters)
    container = factory.SubFactory(
        ContainerFactory,
        config__salt_config__id=factory.SelfAttribute('id'),
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
