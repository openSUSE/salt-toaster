import os
import time
from docker import Client

from config import TIME_LIMIT
from saltcontainers.factories import ImageFactory


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


def build_docker_image(nocache=False):
    docker_client = Client(base_url='unix://var/run/docker.sock')
    path = os.getcwd() + '/docker/'
    image = ImageFactory(docker_client=docker_client, path=path)
    return docker_client.build(
        path=image['path'],
        tag=image['tag'],
        dockerfile=image['dockerfile'],
        pull=True,
        decode=True,
        forcerm=True,
        nocache=nocache
    )
