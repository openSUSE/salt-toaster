import datetime
import os
import re
from collections import namedtuple
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

try:
    from docker import Client
except ImportError:
    print("Warning: no docker module installed! You will be unable to build Docker images.")
    Client = None

Distro = namedtuple("Distro", ["name", "major", "version_separator", "minor"])

OPENSUSE_TUMBLEWEED_MAJOR = "2000"


def parse_distro(distro_str) -> Distro:
    """Use a regular expression to parse a distro_str into its components."""
    name, major, separator, minor = re.match(
        r"""
        (?P<name>[a-z]+)
        (?P<major>\d+)? # major version if it exists
        (?P<separator>[a-zA-Z.]+)? # major-minor separator if it exists
        (?P<minor>\d+)? # minor version if it exists
        """,
        distro_str,
        re.VERBOSE,
    ).groups()

    # allow version comparisons for openSUSE Tumbleweed
    if name == "tumbleweed":
        major = OPENSUSE_TUMBLEWEED_MAJOR

    return Distro(name, major, separator, minor)


def parse_flavor(flavor):
    flavor_major = None
    flavor_major_sec = None
    flavor_minor = None

    if flavor == 'devel':
        # devel means install salt from git repository
        # and because there are no OBS repositories for it
        # we treat it as products so that we don't break the templates commands
        splitted = os.environ.get('BASE_FLAVOR', 'products').split('-')
    else:
        splitted = flavor.split('-')
    if len(splitted) == 1:
        flavor_major, flavor_major_sec, flavor_minor = splitted[0], None, None
    elif len(splitted) == 2:
        flavor_major, flavor_major_sec, flavor_minor = splitted[0], None, splitted[1]
    elif len(splitted) == 3:
        flavor_major, flavor_major_sec, flavor_minor = splitted

    return flavor_major, flavor_major_sec, flavor_minor


def get_salt_version(distro, flavor):
    salt_repo_url = get_salt_repo_url(distro, flavor)
    resp = requests.get("{0}/x86_64".format(salt_repo_url))
    if not resp.status_code == 200:
        return 'n/a'
    soup = BeautifulSoup(resp.content, 'html.parser')
    ex = re.compile(r'^salt-(?P<version>[0-9.]+)-(?P<build>[0-9.]+).x86_64.rpm$')
    salt = soup.find('a', text=ex)
    if not salt:
        return 'n/a'
    match = ex.match(salt.text)
    return match.groupdict()['version']


def get_repo_parts(distro):
    vendor, version_major, separator, version_minor = parse_distro(distro)
    repo_parts = [version_major]
    if version_minor:
        if separator:
            repo_parts.append('{0}{1}'.format(separator, version_minor))
        else:
            repo_parts.append(version_minor)
    return repo_parts


def get_repo_name(distro):
    vendor, version_major, separator, version_minor = parse_distro(distro)
    repo_parts = get_repo_parts(distro)

    if vendor == 'tumbleweed':
        return 'Factory'
    return '_'.join(repo_parts)


def get_salt_repo_name(distro):
    vendor, version_major, separator, version_minor = parse_distro(distro)
    if vendor == 'rhel':
        return 'RHEL_{0}'.format(version_major)
    elif vendor == 'centos':
        return 'CentOS_{0}'.format(version_major)
    elif vendor == 'fedora':
        return 'Fedora_{0}'.format(version_major)
    elif vendor == 'sles':
        return 'SLE_{0}_SP{1}'.format(version_major, version_minor)
    elif vendor == 'leap':
        return 'openSUSE_Leap_{0}.{1}'.format(version_major, version_minor)
    elif vendor == 'tumbleweed':
        return 'openSUSE_Tumbleweed'
    elif vendor == 'ubuntu':
        return 'xUbuntu_{0}.{1}'.format(version_major, version_minor)

    raise Exception('No vendor matched the list of known vendors! %s', vendor)


def get_salt_repo_url_flavor(flavor):
    flavor_major, flavor_major_sec, flavor_minor = parse_flavor(flavor)
    salt_repo_url_parts = [flavor_major]
    if flavor_major_sec:
        salt_repo_url_parts.append(flavor_major_sec)
    if flavor_minor:
        salt_repo_url_parts.append(flavor_minor)
    salt_repo_url_flavor = ':/'.join(salt_repo_url_parts)
    return salt_repo_url_flavor


def get_salt_repo_url(distro, flavor):
    salt_repo_url_flavor = get_salt_repo_url_flavor(flavor)
    salt_repo_name = get_salt_repo_name(distro)
    salt_repo_url = os.environ.get(
        "SALT_REPO_URL",
        "http://{0}/repositories/systemsmanagement:/saltstack:/{1}/{2}/".format(
            os.environ.get("MIRROR", "download.opensuse.org"),
            salt_repo_url_flavor,
            salt_repo_name
        )
    )
    return salt_repo_url


def generate_docker_from(distro) -> str:
    image_registry = os.environ.get('IMAGE_REGISTRY', 'registry.mgr.suse.de')
    if distro.name == 'ubuntu':
        parent_image = '{0}/{1}:{2}.{3}'.format(image_registry, distro.name, distro.major, distro.minor)
    elif distro.name == 'leap':
        parent_image = '{0}/opensuse/{1}:{2}.{3}'.format(image_registry, distro.name, distro.major, distro.minor)
    elif distro.name == 'tumbleweed':
        parent_image = 'opensuse/tumbleweed'
    elif distro.name == 'centos':
        parent_image = '{0}/{1}:{2}'.format(image_registry, distro.name, distro.major)
    else:
        parent_image = '{0}/{1}:{2}.{3}'.format(image_registry, distro.name, distro.major, distro.minor)
    return parent_image


def get_docker_params(distro_str, flavor):
    distro = parse_distro(distro_str)

    return dict(
        vendor=distro.name,
        major=distro.major,
        minor=distro.minor,
        version_separator=distro.version_separator,
        flavor=flavor,
        version=distro_str,
        parent_image=generate_docker_from(distro),
        repo_name=get_repo_name(distro_str),
        salt_repo_url_flavor=get_salt_repo_url_flavor(flavor),
        salt_repo_name=get_salt_repo_name(distro_str),
        salt_repo_url=get_salt_repo_url(distro_str, flavor),
        salt_version=get_salt_version(distro_str, flavor),
    )


def build_docker_image(nocache=False, pull=True):
    if Client is None:
        return

    docker_client = Client(base_url='unix://var/run/docker.sock')

    return docker_client.build(
        tag=os.environ['DOCKER_IMAGE'],
        dockerfile=os.environ['DOCKER_FILE'],
        path=os.getcwd() + '/images/docker/',
        pull=pull,
        decode=True,
        forcerm=True,
        # Allows to invalidate cache for certain steps in Dockerfile
        # https://github.com/docker/docker/issues/22832
        buildargs={'CACHE_DATE': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")},
        nocache=nocache
    )


def generate_dockerfile(version, flavor):
    env = Environment(loader=FileSystemLoader('./templates', followlinks=True))
    TEMPLATES_OVERRIDES = {
        'sles11sp3': 'sles11',
        'sles11sp4': 'sles11',
        'rhel6': 'rhel6',
        'rhel7': 'rhel7',
        'rhel8': 'rhel8',
        'sles12sp3': 'sles12sp3',
        'sles12sp4': 'sles12sp4',
        'sles15': 'sles15',
        'sles15sp1': 'sles15sp1',
        'sles15sp2': 'sles15sp2',
        'leap15.1': 'opensuse',
        'leap15.2': 'opensuse',
        'leap15.3': 'opensuse',
        'tumbleweed': 'tumbleweed',
        'ubuntu1604': 'ubuntu1604',
        'ubuntu1804': 'ubuntu1804',
        'ubuntu2004': 'ubuntu1804',
    }
    parameters = get_docker_params(version, flavor)
    template_name = "{0}.jinja".format(TEMPLATES_OVERRIDES.get(version, parameters['vendor']))
    template = env.get_template(template_name)
    content = template.render(**parameters)
    fpath = Path('docker') / '{}.{}.dockerfile'.format(version, flavor)
    print("Generating {0} using salt-{1}".format(fpath, parameters['salt_version']))
    with open(fpath, 'w') as f:
        f.write(content)
