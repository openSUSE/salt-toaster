set -e
yum -y install swig gcc-c++ libopenssl-devel python-m2crypto
yum -y downgrade test-package-42:0.0-4.1.noarch
yum -y install nmap-ncat
pip install rpdb
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
