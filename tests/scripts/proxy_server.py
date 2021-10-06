#!/usr/bin/env python
import sys
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer


class CustomHandler(SimpleHTTPRequestHandler):
    """ """
    def do_GET(self, *args, **kwargs):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(dict(ret=True))))


Server = HTTPServer(("", int(sys.argv[1])), CustomHandler)
Server.serve_forever()
