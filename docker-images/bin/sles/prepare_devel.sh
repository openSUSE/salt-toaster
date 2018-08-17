set -e

zypper --non-interactive in swig gcc-c++ libopenssl-devel python-m2crypto python-CherryPy
zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive in git curl awk
zypper --non-interactive up zypper libzypp
pip install pytest rpdb
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
