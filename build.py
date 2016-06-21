import argparse
from utils import build_docker_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nocache', action='store_true', default=False)
    args = parser.parse_args()
    for item in build_docker_image(nocache=args.nocache):
        print item.values()[0]


if __name__ == '__main__':
    main()
