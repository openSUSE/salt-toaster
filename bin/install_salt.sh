if [ $DEVEL == "true" ]
    then
        zypper --non-interactive in netcat swig gcc-c++
        pip install M2Crypto pyzmq PyYAML pycrypto msgpack-python jinja2 psutil
        pip install -e $SALT_REPO_MOUNTPOINT
        pip install rpdb
    else
        zypper --non-interactive in salt-master salt-minion salt-proxy
        zypper --non-interactive source-install -D salt
        zypper --non-interactive in --oldpackage test-package=42:0.0
        zypper --non-interactive up zypper libzypp
        bin/unpack_salt.sh
fi
