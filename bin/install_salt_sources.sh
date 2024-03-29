#!/bin/bash
set -e

if [ "$FLAVOR" != "devel" ]
    then
        if [[ "$DISTRO" =~ ^rhel ]]
            then
                bin/rhel_unpack_salt.sh
        elif [[ "$DISTRO" =~ ^(sles|leap) ]]
            then
                bin/sles_unpack_salt.sh
        elif [[ "$DISTRO" =~ ^ubuntu ]]
            then
                bin/ubuntu_unpack_salt.sh
        fi
fi
