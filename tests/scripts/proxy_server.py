#!/usr/bin/env python
import sys
import json
import BaseHTTPServer
import SocketServer


class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """ """
    def do_GET(self, *args, **kwargs):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(
            json.dumps(dict(ret=True))
        )


Server = SocketServer.TCPServer(("", int(sys.argv[1])), CustomHandler)
Server.serve_forever()
