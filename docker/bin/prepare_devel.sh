set -e
zypper --non-interactive in \
    swig \
    gcc-c++ \
    libopenssl-devel \
    python-m2crypto \
    python-pycrypto \
    python-msgpack-python \
    python-PyYAML \
    python-Jinja2 \
    python-psutil \
    python-pyzmq

zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive in netcat
pip install rpdb

mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
