# -*- coding: utf-8 -*-

import os
import sys
import yaml
import textwrap
from invoke import run, task, call


default_config = dict(
    registry='registry.mgr.suse.de',
    version='sles12sp3',
    flavor='products',
    toaster_mountpoint='salt-toaster',
    root_mountpoint='salt/src'
)


def _get_config(user_supplied_config):
    """\
    Set up the config map.
    """
    config = user_supplied_config
    config.update(dict(
        salt_repo_mountpoint='{}/salt-devel'.format(
            config.get('root_mountpoint')),
        salt_tests='{}/salt-*/tests'.format(config.get('root_mountpoint')),
        docker_volumes='-v "{}/:{}"'.format(os.getcwd(),
                                            config.get('toaster_mountpoint')),
    ))

    config['docker_registry'] = user_supplied_config.get(
        'docker_registry',
        config.get('default_registry'))
    config['version'] = user_supplied_config.get('version',
                                                 config.get('default_version'))
    config['flavor'] = user_supplied_config.get('flavor',
                                                config.get('default_flavor'))
    config['flavor'] = user_supplied_config.get('flavor',
                                                config.get('default_flavor'))
    config['docker_image'] = user_supplied_config.get(
        'docker_image', "{docker_registry}/toaster-{version}-{flavor}".format(
            **config))
    config['docker_file'] = user_supplied_config.get(
        'docker_file', "Dockerfile.{version}.{flavor}".format(**config))

    if os.environ.get('BUILD_ID') and not \
       (user_supplied_config.get('docker_mem') or \
        user_supplied_config.get('docker_cpus')):
        config['docker_mem'] = "2G"
        config['docker_cpus'] = "1.5"
    else:
        config['docker_mem'] = user_supplied_config.get('docker_mem')
        config['docker_cpus'] = user_supplied_config.get('docker_cpus')

    # FIXME: When is this needed and where should this come from??????
    config['minion_version'] = config.get('version')
    config['minion_flavor'] = config.get('flavor')

    config['exports'] = textwrap.dedent("""
        -e "salt_tests={salt_tests}" \
        -e "version={version}" \
        -e "flavor={flavor}" \
        -e "docker_image={docker_image}" \
        -e "docker_file={docker_file}" \
        -e "minion_version={minion_version}" \
        -e "minion_flavor={minion_flavor}" \
        -e "root_mountpoint={root_mountpoint}" \
        -e "salt_repo_mountpoint={salt_repo_mountpoint}" \
        -e "toaster_mountpoint={toaster_mountpoint}"
    """).format(**config)
    return config


@task
def docker_shell(c,
        registry=default_config.get('registry'),
        version=default_config.get('version'),
        flavor=default_config.get('flavor'),
        toaster_mountpoint=default_config.get('salt-toaster'),
        root_mountpoint=default_config.get('salt/src'),
        docker_mem=None,
        docker_cpus=None):
    """\
    Opening up a Docker shell for the provided setup.
    """
    config = _get_config(dict(default_registry=registry,
                              default_version=version,
                              default_flavor=flavor,
                              toaster_mountpoint=toaster_mountpoint,
                              root_mountpoint=root_mountpoint,
                              docker_mem=docker_mem,
                              docker_cpus=docker_cpus))
    print(config)
    # This is just for the example. Nothing is passed here and starting
    # the docker container should probably done via dockerpy.
    c.run('docker run -ti --rm -e "CMD=/bin/bash" ubuntu', pty=True)