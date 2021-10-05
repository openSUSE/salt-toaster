import os
import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import saltrepoinspect as sri

try:
    from docker import Client
except ImportError as ex:
    print("Warning: no docker module installed! You will be unable to build Docker images.")
    Client = None


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
    parameters = sri.get_docker_params(version, flavor)
    template_name = "{0}.jinja".format(TEMPLATES_OVERRIDES.get(version, parameters['vendor']))
    template = env.get_template(template_name)
    content = template.render(**parameters)
    fpath = Path('docker') / 'Dockerfile.{}.{}'.format(version, flavor)
    print("Generating {0} using salt-{1}".format(fpath, parameters['salt_version']))
    with open(fpath, 'w') as f:
        f.write(content)
