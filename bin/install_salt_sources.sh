set -e

if [ "$DEVEL" == "true" ]
    then
        docker/bin/prepare_devel.sh
        pip install -e $SALT_REPO_MOUNTPOINT
    else
        if [[ "$VERSION" =~ ^rhel ]]
            then
                bin/rhel_unpack_salt.sh
            else
                docker/bin/install_salt.sh
                bin/sles_unpack_salt.sh
        fi
fi
