#!/usr/bin/env python


import sys
import requests
import argparse
import py.path


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, dest='url', type=str)
    parser.add_argument('--etag-file', required=True, dest='etagfile', type=str)

    params = parser.parse_args()

    etag_file = py.path.local(params.etagfile)

    if not etag_file.exists():
        response = requests.get(params.url, stream=True)
        etag_file.write(response.headers['ETag'])

    etag = etag_file.read('rb')

    response = requests.get(
        params.url, headers={'If-None-Match': '{0}'.format(etag)})

    if response.status_code != 304:
        with open('etag', 'wb') as f:
            f.write(response.headers['ETag'])
        sys.exit(0)

    sys.exit(1)
