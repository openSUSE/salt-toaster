#!/usr/bin/python
import os
import sys
import socket


def setup_socket():
    '''
    Setup socket listener.
    '''
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind(('127.0.0.1', int(sys.argv[1])))
    skt.listen(1)
    conn, addr = skt.accept()
    data = conn.recv(1024)
    conn.close()

    with open(sys.argv[2], 'wb') as dump:
        dump.write(data)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: {} port /path/to/output.file".format(os.path.basename(sys.argv[0])))
        sys.exit(1)
    else:
        setup_socket()
