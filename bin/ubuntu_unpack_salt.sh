#!/bin/bash
set -e

export SALT_SOURCES="/salt"

if [ -d $SALT_SOURCES ]; then
    rm -rf $SALT_SOURCES
fi

rm -rf salt*ds*
apt source salt-common
mkdir -p $SALT_SOURCES/src/
cp -R salt* $SALT_SOURCES/src/
rm -rf salt*ds*

exit 0
