set -e

if [ "$FLAVOR" != "devel" ]
    then
        if [[ "$VERSION" =~ ^rhel ]]
            then
                bin/rhel_unpack_salt.sh
        elif [[ "$VERSION" =~ ^sles ]]
            then
                /root/bin/install_salt.sh
                bin/sles_unpack_salt.sh
        fi
fi
