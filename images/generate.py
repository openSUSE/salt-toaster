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

INCLUDE: Set[DFC] = set()

EXCLUSIONS: Set[DFC] = {
    DFC(
        "tumbleweed",
        "products-next",
    ),  # NOTE: docker file was manually adjusted. fix before enabling
    DFC(
        "tumbleweed",
        "products-next-testing",
    ),  # NOTE: docker file was manually adjusted. fix before enabling
    DFC("sles11sp4", "products"),
    DFC("sles11sp4", "products-testing"),
    DFC("sles11sp4", "products-3000"),
    DFC("sles11sp4", "products-3000-testing"),
    DFC("sles11sp4", "products-next"),
    DFC("sles11sp4", "products-next-testing"),
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate Dockerfiles for Salt-Toaster"
    )
    parser.add_argument(
        "-d",
        "--distro",
        "--distros",
        dest="distros",
        nargs="+",
        help=" ".join(
            [
                "The distro(s) to generate Dockerfiles for. If used together",
                "with --flavor(s), only distro(s) * flavor(s) are generated.",
                "Otherwise, all flavors is generated for each distro.",
            ]
        ),
        default=DISTROS,
    )
    parser.add_argument(
        "-f",
        "--flavor",
        "--flavors",
        dest="flavors",
        nargs="+",
        help=" ".join(
            [
                "The flavor(s) to generate Dockerfiles for. If used together",
                "with --distro(s), only distro(s) * flavor(s) are generated.",
                "Otherwise, this flavors is generated for each distro.",
            ]
        ),
        default=FLAVORS,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate Dockerfiles for all possible distro + flavor combinations.",
    )
    parser.add_argument(
        "--skip-included",
        action="store_true",
        help="Don't generate Dockefiles from the INCLUDE set.",
    )
    args = parser.parse_args()

    if not any([args.all, args.distros, args.flavors]):
        print(
            " ".join(
                [
                    "Please specify either --all, --distro(s) or --flavor(s).",
                    "--distro(s) and --flavor(s) can be combined.",
                ]
            )
        )
        exit(1)
    elif args.all and (args.distros or args.flavors):
        print("Additional arguments not allowed with --all")
        exit(1)

    if args.all:
        requested: Set[DFC] = {
            DFC(distro, flavor)
            for (distro, flavor) in itertools.product(DISTROS, FLAVORS)
        }
    else:
        requested: Set[DFC] = {
            DFC(distro, flavor)
            for (distro, flavor) in itertools.product(args.distros, args.flavors)
        }
        if not args.skip_included:
            requested |= INCLUDE

    allowed = requested - EXCLUSIONS
    disallowed = requested & EXCLUSIONS

    for combination in sorted(allowed, key=lambda x: x.distro):
        generate_dockerfile(*combination)

    print("Excluded combinations:")
    for combination in sorted(disallowed, key=lambda x: x.distro):
        print(f"Distro: {combination.distro} - Flavor: {combination.flavor}")


if __name__ == "__main__":
    main()
