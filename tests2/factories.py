import os
import json
import factory
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
    root = None

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
                "/home/mdinca/repositories/salt-toaster/": {
                    'bind': "/salt-toaster/",
                    'mode': 'rw'
                }
            }
        )


class ContainerConfigFactory(BaseFactory):
    salt_config = factory.SubFactory(SaltConfigFactory)
    name = factory.Faker('word')
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

    def run(self, command, to_json=True):
        cmd_exec = self['docker_client'].exec_create(
            self['config']['name'], cmd=command)
        output = self['docker_client'].exec_start(cmd_exec['Id'])
        if to_json:
            return json.loads(output)
        return output


class ContainerFactory(BaseFactory):

    docker_client = None
    config = factory.SubFactory(ContainerConfigFactory)

    class Meta:
        model = ContainerModel

    @classmethod
    def build(cls, **kwargs):
        obj = super(ContainerFactory, cls).build(**kwargs)
        obj['docker_client'].create_container(**obj['config'])
        obj['docker_client'].start(obj['config']['name'])
        return obj


class MasterFactory(BaseFactory):
    container = factory.SubFactory(ContainerFactory)

    class Meta:
        model = dict

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


class MinionFactory(BaseFactory):
    container = factory.SubFactory(ContainerFactory)

    class Meta:
        model = dict

    @classmethod
    def build(cls, **kwargs):
        obj = super(MinionFactory, cls).build(**kwargs)
        docker_client = obj['container']['docker_client']
        res = docker_client.exec_create(
            obj['container']['config']['name'],
            cmd='salt-minion -d -l debug'
        )
        docker_client.exec_start(res['Id'])
        return obj
