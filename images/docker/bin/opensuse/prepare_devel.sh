set -e

zypper --non-interactive in swig gcc-c++ libopenssl-devel
zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive in git curl awk vim
zypper --non-interactive up zypper libzypp
zypper --non-interactive in python3-pytest python3-PyYAML python3-Jinja2 python3-pyzmq python3-M2Crypto python3-mock python3-apache-libcloud python3-six python3-dateutil
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
