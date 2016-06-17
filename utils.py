import os
import time
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
        success = func()
        if success is not True:
            time.sleep(1)
            continue
    return success


def get_docker_build_params(version, flavor, path):
    tag_pattern = 'registry.mgr.suse.de/toaster-{0}-{1}'
    file_pattern = 'Dockerfile.{0}.{1}'
    return dict(
        tag=tag_pattern.format(version, flavor),
        dockerfile=file_pattern.format(version, flavor),
        pull=True,
        decode=True,
        forcerm=True
        # nocache=True
    )


def build_docker_image(version, flavor):
    docker_client = Client(base_url='unix://var/run/docker.sock')
    path = os.getcwd() + '/docker/'
    params = get_docker_build_params(version, flavor, path)
    return docker_client.build(path=path, **params)
