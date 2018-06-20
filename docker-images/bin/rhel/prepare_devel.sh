set -e

yum -y --nogpgcheck install swig gcc-c++ libopenssl-devel python-m2crypto python-CherryPy
yum -y --nogpgcheck install test-package-42:0.0-3.2.noarch
yum -y --nogpgcheck install git curl
yum -y install nmap-ncat
pip install pytest rpdb
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
