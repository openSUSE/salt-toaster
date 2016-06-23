#!/bin/bash
#
# Author: bo@suse.de
#
# Prepare environment for the Salt Toaster "on-the-fly"


#
# Check if all required commands are in place.
#
function check_requirements() {
    for cmd in "virtualenv" "python" "pip" "docker"; do
	cmd_pth=$(which $cmd 2>/dev/null)
	if [ -z "$cmd_pth" ]; then
	    echo "Error: command '$cmd' is missing"
	    exit 1;
	fi
    done

    # RPM is "python-devel", Deb is "python-dev"
    # Goes on common check
    for pkg in "python-dev" "gcc" "make"; do
	pkg_name=""
	if [ -n "$(which dpkg 2>/dev/null)" ]; then
	    pkg_name=$(dpkg -l $pkg | grep $pkg)
	elif [ -n "$(which rpm 2>/dev/null)" ]; then
	    pkg_name=$(rpm -qa | grep $pkg)
	fi
	if [ -z "$pkg_name" ]; then
	    echo "Error: Development stack needs to be installed"
	    echo "       python dev, gcc, make etc"
	    exit 1;
	fi
    done

    if [ -z "$(ps uax | grep docker | grep daemon)" ]; then
	echo "Error: Docker daemon should run"
	exit 1;
    fi

    python -c "import docker" 2>/dev/null
    if [ $? -ne 0 ]; then
	echo "Error: Python docker bindings needs to be installed."
	exit 1;
    fi
}

function create_virtual_env() {
    virtualenv --system-site-packages $1
    source $1/bin/activate
    pip install -r requirements.txt
}

if [ -z $1 ]; then
    echo -e "Usage:\n"
    echo -e "\tprepare_environment /path/to/environment"
else
    check_requirements
    create_virtual_env $1
fi
