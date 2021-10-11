import os
import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

try:
    from docker import Client
except ImportError as ex:
    print("Warning: no docker module installed! You will be unable to build Docker images.")
    Client = None


# FIXME: Deduplicate with second and third copy of this


import re
import os
import requests
from collections import namedtuple
from bs4 import BeautifulSoup

Distro = namedtuple("Distro", ["name", "major", "version_separator", "minor"])


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

    # We use names like opensuse152 for openSUSE Leap 15.2
    if name == "opensuse":
        minor = major[-1]

    # allow version comparisons for openSUSE Tumbleweed
    if name == "tumbleweed":
        major = "2000"

    return Distro(name, major, separator, minor)

def parse_version(version):
    """Deprecated. Use parse_distro instead."""
    exp = '(?P<vendor>sles|rhel|centos|ubuntu|opensuse|tumbleweed)(?:(?P<major>\d{1,2})(?:(?P<sp>sp)*(?P<minor>\d+))?)?'
    return re.match(exp, version).groups()


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
        flavor_major, flavor_major_sec, flavor_minor = flavor, None, None
    elif len(splitted) == 2:
        flavor_major, flavor_major_sec, flavor_minor = splitted[0], None, splitted[1]
    elif len(splitted) == 3:
        flavor_major, flavor_major_sec, flavor_minor = splitted

    return flavor_major, flavor_major_sec, flavor_minor


def get_salt_version(version, flavor):
    salt_repo_url = get_salt_repo_url(version, flavor)
    resp = requests.get("{0}/x86_64".format(salt_repo_url))
    if not resp.status_code == 200:
        return 'n/a'
    soup = BeautifulSoup(resp.content, 'html.parser')
    ex = re.compile(r'^salt-(?P<version>[0-9\.]+)-(?P<build>[0-9\.]+).x86_64.rpm$')
    salt = soup.find('a', text=ex)
    if not salt:
        return 'n/a'
    match = ex.match(salt.text)
    return match.groupdict()['version']


def get_repo_parts(version):
    vendor, version_major, separator, version_minor = parse_version(version)
    repo_parts = [version_major]
    if version_minor:
        if separator:
            repo_parts.append('{0}{1}'.format(separator, version_minor))
        else:
            repo_parts.append(version_minor)
    return repo_parts


def get_repo_name(version, flavor):
    vendor, version_major, separator, version_minor = parse_version(version)
    repo_parts = get_repo_parts(version)
    if vendor == 'SLES' and version_major == '11':
        repo_name = 'SLE_11_SP4'
    if vendor == 'tumbleweed':
        repo_name = 'Factory'
    else:
        repo_name = '_'.join(repo_parts)
    return repo_name


def get_salt_repo_name(version, flavor):
    vendor, version_major, separator, version_minor = parse_version(version)
    repo_name = get_repo_name(version, flavor)
    salt_repo_name = 'SLE_{0}'.format(repo_name).upper()
    if vendor == 'rhel':
        salt_repo_name = '{0}_{1}'.format(vendor, repo_name)

    if version in ['sles11sp3', 'sles11sp4']:
        salt_repo_name = 'SLE_11_SP4'

    return salt_repo_name


def get_salt_repo_url_flavor(flavor):
    flavor_major, flavor_major_sec, flavor_minor = parse_flavor(flavor)
    salt_repo_url_parts = [flavor_major]
    if flavor_major_sec:
        salt_repo_url_parts.append(flavor_major_sec)
    if flavor_minor:
        salt_repo_url_parts.append(flavor_minor)
    salt_repo_url_flavor = ':/'.join(salt_repo_url_parts)
    return salt_repo_url_flavor



def get_salt_repo_url(version, flavor):
    salt_repo_url_flavor = get_salt_repo_url_flavor(flavor)
    salt_repo_name = get_salt_repo_name(version, flavor)
    salt_repo_url = os.environ.get(
        "SALT_REPO_URL",
        "http://{0}/repositories/systemsmanagement:/saltstack:/{1}/{2}/".format(
            os.environ.get("MIRROR", "download.opensuse.org"),
            salt_repo_url_flavor,
            salt_repo_name.upper()
        )
    )
    return salt_repo_url


def get_docker_params(distro_str, flavor):
    distro = parse_distro(distro_str)
    flavor_major, flavor_major_sec, flavor_minor = parse_flavor(flavor)
    repo_name = get_repo_name(distro_str, flavor)
    salt_repo_name = get_salt_repo_name(distro_str, flavor)
    salt_repo_url_flavor = get_salt_repo_url_flavor(flavor)
    parent_image = 'registry.mgr.suse.de/{0}'.format(distro_str)
    if distro.name == 'ubuntu':
        parent_image = '{0}:{1}.{2}'.format(distro.name, distro.major, distro.minor)
    elif distro.name == 'tumbleweed':
        parent_image = 'opensuse/tumbleweed'
    salt_repo_url = get_salt_repo_url(distro_str, flavor)
    salt_version = get_salt_version(distro_str, flavor)

    return dict(
        vendor=distro.name,
        major=distro.major,
        minor=distro.minor,
        version_separator=distro.version_separator,
        flavor=flavor,
        version=distro_str,
        parent_image=parent_image,
        flavor_major=flavor_major,
        flavor_major_sec=flavor_major_sec,
        flavor_minor=flavor_minor,
        repo_name=repo_name,
        salt_repo_url_flavor=salt_repo_url_flavor,
        salt_repo_name=salt_repo_name,
        salt_repo_url=salt_repo_url,
        salt_version=salt_version,
    )


##############


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
        'opensuse423': 'opensuse',
        'opensuse150': 'opensuse',
        'opensuse151': 'opensuse',
        'tumbleweed': 'tumbleweed',
        'ubuntu1604': 'ubuntu1604',
        'ubuntu1804': 'ubuntu1804',
    }
    parameters = get_docker_params(version, flavor)
    template_name = "{0}.jinja".format(TEMPLATES_OVERRIDES.get(version, parameters['vendor']))
    template = env.get_template(template_name)
    content = template.render(**parameters)
    fpath = Path('docker') / 'Dockerfile.{}.{}'.format(version, flavor)
    print("Generating {0} using salt-{1}".format(fpath, parameters['salt_version']))
    with open(fpath, 'w') as f:
        f.write(content)
