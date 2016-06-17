import os
from utils import build_docker_image

VERSION = os.environ['VERSION']
FLAVOR = os.environ.get('FLAVOR', 'products')


if __name__ == '__main__':
    for item in build_docker_image(VERSION, FLAVOR):
        print item.values()[0]
