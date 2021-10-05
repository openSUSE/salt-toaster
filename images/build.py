import re
import argparse
from utils import build_docker_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nocache', action='store_true', default=False)
    parser.add_argument('--nopull', action='store_true', default=False)
    args = parser.parse_args()
    content = ''
    stream = build_docker_image(nocache=args.nocache, pull=not args.nopull)
    for item in stream:
        if 'error' in item:
            raise Exception(item['error'])
        buff = item.get('stream', item.get('status', ''))

        if not content or re.search('.+\[[. ]*$', content):
            content += buff

        if not re.search('.+\[[. ]*$', content):
            if not isinstance(content, str):
                print(content.encode('utf8'))
            else:
                print(content)
            content = ''


if __name__ == '__main__':
    main()
