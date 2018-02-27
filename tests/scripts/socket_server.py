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

    with open(sys.argv[2], 'w') as dump:
        dump.write(data)


def daemonize(stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"):
    '''
    Daemonize current script
    '''
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0)
    except OSError as e: 
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror) )
        sys.exit(1)

    os.chdir("/") 
    os.umask(0) 
    os.setsid() 

    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0)
    except OSError as e: 
        sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror) )
        sys.exit(1)

    stdin_par = os.path.dirname(stdin)
    stdout_par = os.path.dirname(stdout)
    stderr_par = os.path.dirname(stderr)
    if not stdin_par:
        os.path.makedirs(stdin_par)
    if not stdout_par:
        os.path.makedirs(stdout_par)
    if not stderr_par:
        os.path.makedirs(stderr_par)

    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'ab+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: {} port /path/to/output.file".format(os.path.basename(sys.argv[0])))
        sys.exit(1)
    else:
        # This has to go background on its own,
        # because shell tricks won't work :-(
        daemonize()
        setup_socket()
