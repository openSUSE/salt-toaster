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
if [ -f /usr/bin/yumdownloader ]; then
yumdownloader --source salt
else
dnf download --source salt
fi
rpm -ivh salt-*.src.rpm
rm -f salt-*.src.rpm
rpmbuild -bp /usr/src/packages/SPECS/salt.spec
mkdir -p $SALT_SOURCES/src/
cp -R /usr/src/packages/BUILD/salt-* $SALT_SOURCES/src/
exit 0
