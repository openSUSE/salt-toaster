import argparse
import itertools
from utils import generate_dockerfile, generate_pytest_config


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
    parser.add_argument('--version')
    parser.add_argument('--flavor')
    parser.add_argument('--all', action="store_true", default=False)
    args = parser.parse_args()
    if args.all:
        matrix = itertools.product(VERSIONS, FLAVORS)
        for params in matrix:
            generate_dockerfile(*params)
            generate_pytest_config(*params)
    else:
        generate_dockerfile(args.version, args.flavor)
        generate_pytest_config(args.version, args.flavor)


if __name__ == '__main__':
    main()
