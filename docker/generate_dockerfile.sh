#!/bin/bash

echo "# Container used to run salt tests focusing on SUSE Manager use cases" > $ROOT/Dockerfile
echo "#" >> $ROOT/Dockerfile
echo "# NAME                  $CONTAINER_NAME" >> $ROOT/Dockerfile
echo "# VERSION               $VERSION" >> $ROOT/Dockerfile
echo "" >> $ROOT/Dockerfile


cat docker/Dockerfile.template | while read line; do echo $(eval echo `echo -e $line`); done >> $ROOT/Dockerfile

echo $VERSION > $DESTINATION/VERSION
