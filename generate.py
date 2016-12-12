import argparse
import itertools
from utils import generate_pytest_config


VERSIONS = [
    'rhel6',
    'rhel7',
    'sles11sp3',
    'sles11sp4',
    'sles12',
    'sles12sp1',
    'sles12sp2'
]


FLAVORS = [
    'products',
    'products-next',
    'products-testing',
    'testing',
    'next'
]


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action="store_true", default=False)
    group.add_argument('--version-and-flavor', nargs=2)
    args = parser.parse_args()
    if args.all:
        matrix = itertools.product(VERSIONS, FLAVORS)
        for params in matrix:
            generate_dockerfile(*params)
            generate_pytest_config(*params)
    else:
        generate_dockerfile(*args.version_and_flavor)
        generate_pytest_config(*args.version_and_flavor)


if __name__ == '__main__':
    main()
