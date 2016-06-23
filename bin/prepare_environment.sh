#!/bin/bash
#
# Author: bo@suse.de
#
# Prepare environment for the Salt Toaster "on-the-fly"


#
# Check if all required commands are in place.
#
function check_requirements() {
    for cmd in "virtualenv" "python" "pip"; do
	cmd_pth=$(which $cmd 2>/dev/null)
	if [ -z "$cmd_pth" ]; then
	    echo "Error: command '$cmd' is missing"
	    exit;
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
	    exit;
	fi
    done
}

function create_virtual_env() {
    echo "hello"
}

check_requirements
