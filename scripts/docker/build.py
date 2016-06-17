from utils import build_docker_image


if __name__ == '__main__':
    for item in build_docker_image():
        print item.values()[0]
