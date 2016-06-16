#!/bin/bash

export SALT_SOURCES="/salt"

#
# Rip away the exact sources from the tested package.
# As long this is the corresponding source package... :-/
#
function collect_sources {
    mkdir $SALT_SOURCES/src
    SRC="/usr/src/packages"
    # Always install source RPM
    # zypper --non-interactive source-install salt
    if [ ! -f "$SRC/SPECS/salt.spec" ]; then
	msg="Cannot find salt.spec file."
	skip_tests "\${msg}"
	exit 0
    else
	cp $SRC/SPECS/salt.spec $SALT_SOURCES/src
    fi

    # Get patches first
    for p_file in $(cat $SRC/SPECS/salt.spec | grep -i '^patch' | awk '{print $2}'); do
	if [ ! -f "$SRC/SOURCES/$p_file" ]; then
	    msg="Missing patch: $p_file"
	    skip_tests "\${msg}"
	    exit 0
	else
	    cp $SRC/SOURCES/$p_file $SALT_SOURCES/src
	fi
    done

    # Find sources
    if [ -e /usr/bin/rpmspec ]; then
        SPECREADER="rpmspec -P"
    else
        SPECREADER="cat"
    fi
    name_version=$(rpm -q --qf "%{name}-%{version}\n" --specfile $SRC/SPECS/salt.spec | head -1)
    for s_file in $($SPECREADER $SRC/SPECS/salt.spec | grep -i '^source' | awk '{print $2}'); do
	s_file=$(echo $s_file | sed -e 's/.*\///g')
	if $(echo $s_file | grep -F '%{name}-%{version}' >/dev/null); then
            s_file=$(echo $s_file | sed "s/%{name}-%{version}/$name_version/")
        fi
	if [ ! -f "$SRC/SOURCES/$s_file" ]; then
	    msg="Missing source file: $s_file"
	    skip_tests "\${msg}"
	    exit 0
	else
	    cp $SRC/SOURCES/$s_file $SALT_SOURCES/src
	fi
    done
}


#
# Prepare tarball (toss in patches etc)
#
function prepare_sources {
    cd $SALT_SOURCES/src
    quilt setup salt.spec > /dev/null
    cd salt*
    quilt -a push > /dev/null
}


#
# Main
#
if [ -d $SALT_SOURCES ]; then
    rm -rf $SALT_SOURCES
fi

mkdir $SALT_SOURCES
PWD=$(pwd)
collect_sources
prepare_sources
