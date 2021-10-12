import argparse
import itertools
from collections import namedtuple
from typing import Set

from utils import generate_dockerfile

DFC = namedtuple("DistroFlavorCombination", ("distro", "flavor"))

DISTROS = {
    "rhel7",
    "rhel8",
    "sles11sp4",
    "sles12sp3",
    "sles12sp4",
    "sles12sp5",
    "sles15",
    "sles15sp1",
    "sles15sp2",
    "sles15sp3",
    "ubuntu1804",
    "ubuntu2004",
    "centos7",
    "leap15.1",
    "leap15.2",
    "leap15.3",
    "tumbleweed",
}

FLAVORS = {
    "products",
    "products-testing",
    "products-3000",
    "products-3000-testing",
    "products-next",
    "products-next-testing",
    "devel",
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate Dockerfiles for Salt-Toaster. The default is to generate files for all combinations."
    )
    parser.add_argument(
        "-d",
        "--distro",
        "--distros",
        dest="distros",
        nargs="+",
        help="The distro(s) to generate Dockerfiles for. If used together with --flavor(s), only distro(s) * flavor(s)"
             " are generated. Otherwise, all flavors is generated for each distro.",
        default=DISTROS,
    )
    parser.add_argument(
        "-f",
        "--flavor",
        "--flavors",
        dest="flavors",
        nargs="+",
        help="The flavor(s) to generate Dockerfiles for. If used together with --distro(s), only distro(s) * flavor(s)"
             " are generated. Otherwise, this flavors is generated for each distro.",
        default=FLAVORS,
    )
    args = parser.parse_args()

    requested: Set[DFC] = {
        DFC(distro, flavor)
        for (distro, flavor) in itertools.product(args.distros, args.flavors)
    }

    for combination in sorted(requested, key=lambda x: x.distro):
        generate_dockerfile(*combination)


if __name__ == "__main__":
    main()
