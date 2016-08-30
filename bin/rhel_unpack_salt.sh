#!/bin/bash
set -e

export SALT_SOURCES="/salt"

if [ -d $SALT_SOURCES ]; then
    rm -rf $SALT_SOURCES
fi

mkdir -p /usr/src/packages/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
echo '%_topdir /usr/src/packages' > ~/.rpmmacros
echo '%_tmppath %{_topdir}/tmp' >> ~/.rpmmacros
rm -f salt-*.src.rpm
yum clean expire-cache
yumdownloader --source salt
rpm -ivh salt-*.src.rpm
rm -f salt-*.src.rpm
rpmbuild -bp /usr/src/packages/SPECS/salt.spec
mkdir -p $SALT_SOURCES/src/
ln -s /usr/src/packages/BUILD/salt-* $SALT_SOURCES/src/
pip install pytest
