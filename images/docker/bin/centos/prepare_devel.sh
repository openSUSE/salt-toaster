set -e

yum -y install swig gcc-c++ openssl-devel openssl-libs m2crypto python-cherrypy python-tornado python-jinja2 python-futures python-zmq PyYAML python-msgpack python-mock python-libcloud python-dateutil
yum -y install test-package
yum -y install git curl
yum -y install nmap-ncat || true
mkdir -p /etc/salt
touch /etc/salt/master
touch /etc/salt/minion
