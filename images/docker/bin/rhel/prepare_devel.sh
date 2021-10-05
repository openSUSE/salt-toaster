set -e

yum -y --nogpgcheck install swig gcc-c++ openssl-devel openssl-libs m2crypto python-cherrypy python-msgpack-python python-tornado python-jinja2 python-futures python-zmq
yum -y --nogpgcheck install test-package
yum -y --nogpgcheck install git curl
yum -y install nmap-ncat || true
pip install pytest rpdb
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
