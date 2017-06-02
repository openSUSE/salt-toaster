import datetime
import os
import re
import time
from jinja2 import Environment, FileSystemLoader
from py.path import local as path
from docker import Client

from config import TIME_LIMIT


class TimeLimitReached(Exception):

    """Used in tests to limit blocking time."""


def time_limit_reached(start_time):
    if TIME_LIMIT < (time.time() - start_time):
        raise TimeLimitReached


def retry(func):
    success = False
    start_time = time.time()
    while not success and not time_limit_reached(start_time):
        print('retry: ' + func.func_name)
        success = func() is True
        if success is not True:
            time.sleep(1)
            continue
    return success


def build_docker_image(nocache=False, pull=True):
    docker_client = Client(base_url='unix://var/run/docker.sock')

    return docker_client.build(
        tag=os.environ['DOCKER_IMAGE'],
        dockerfile=os.environ['DOCKER_FILE'],
        path='https://gitlab.suse.de/mdinca/toaster-docker-support.git#dev:docker',
        # path="https://{0}@gitlab.suse.de/mdinca/toaster-docker-support.git#master:docker".format(
        #     os.environ.get('GITLAB_AUTH')),
        pull=pull,
        decode=True,
        forcerm=True,
        # Allows to invalidate cache for certains steps in Dockerfile
        # https://github.com/docker/docker/issues/22832
        buildargs={'CACHE_DATE': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")},
        nocache=nocache
    )


def get_template_parameters(version, flavor):
    vendor, version_major, separator, version_minor = re.match(
        '(?P<vendor>sles|rhel)(?P<major>\d{1,})(?:(?P<sp>sp)(?P<minor>\d{1,}))*',
        version).groups()
    flavor_major, flavor_minor = flavor.split('-') if '-' in  flavor else (flavor, None)
    parent_image = 'registry.mgr.suse.de/{}'.format(version)
    repo_parts = [version_major]
    if version_minor:
        repo_parts.append('{}{}'.format(separator, version_minor))
    novel_repo_name = '-'.join(repo_parts).upper()
    repo_name = '_'.join(repo_parts)
    repo_label = ' '.join(repo_parts).upper()
    salt_repo_name = 'SLE_{}'.format(repo_name).upper()
    if vendor == 'rhel':
        salt_repo_name = '{}_{}'.format(vendor, repo_name)
    salt_repo_url_parts = [flavor_major]
    if flavor_minor:
        salt_repo_url_parts.append(flavor_minor)
    salt_repo_url_flavor = ':/'.join(salt_repo_url_parts)

    return dict(
        vendor = vendor,
        major=version_major,
        minor=version_minor,
        version_separator=separator,
        flavor=flavor,
        version=version,
        parent_image=parent_image,
        flavor_major=flavor_major,
        flavor_minor=flavor_minor,
        repo_name=repo_name,
        novel_repo_name=novel_repo_name,
        repo_label=repo_label,
        salt_repo_url_flavor=salt_repo_url_flavor,
        salt_repo_name=salt_repo_name)


def apply_overrides(params):
    if params['version'] in ['sles11sp3', 'sles11sp4']:
        params['salt_repo_name'] = 'SLE_11_SP4'
    return params


def generate_pytest_config(version, flavor):
    parameters = get_template_parameters(version, flavor)
    env = Environment(loader=FileSystemLoader('./configs/templates', followlinks=True))
    template = env.get_template(parameters['vendor'])
    content = template.render(**parameters)
    (path('configs') / 'suse.tests'/ version / "{}.cfg".format(flavor)).write(content)
