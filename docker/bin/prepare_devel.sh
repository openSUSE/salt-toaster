set -e
zypper --non-interactive in swig gcc-c++ libopenssl-devel python-m2crypto

zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive in netcat
pip install pytest rpdb salttesting psutil

mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
