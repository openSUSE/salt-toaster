set -e
zypper --non-interactive in netcat swig gcc-c++ libopenssl-devel
zypper --non-interactive in --oldpackage test-package=42:0.0
pip install M2Crypto pyzmq PyYAML pycrypto msgpack-python jinja2 psutil
pip install rpdb

mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
