set -e

if [ "$DEVEL" == "true" ]
    then
        docker/bin/prepare_devel.sh
        pip install -e $SALT_REPO_MOUNTPOINT
    else
        zypper -n install quilt rpmbuild
        docker/bin/install_salt.sh
        zypper --non-interactive source-install -D salt
        bin/unpack_salt.sh
fi
