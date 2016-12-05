import os
import time
import tarfile
import py.path
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
        path=os.getcwd() + '/docker/',
        pull=pull,
        decode=True,
        forcerm=True,
        nocache=nocache
    )


def upload(container, source, destination, tmpdir_factory):
    arch = tmpdir_factory.mktemp("archive") / 'arch.tar'
    source = py.path.local(source)
    with tarfile.open(arch.strpath, mode='w') as archive:
        if source.isdir():
            for item in source.listdir():
                archive.add(
                    item.strpath,
                    arcname=item.strpath.replace(source.strpath, '.'))
        elif source.isfile():
            archive.add(source.strpath, arcname=source.basename)

    container.run('mkdir -p {0}'.format(destination))
    container['config']['docker_client'].put_archive(
        container['config']['name'], destination, arch.read())
