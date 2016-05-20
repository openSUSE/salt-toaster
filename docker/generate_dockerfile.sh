#!/bin/bash

echo "# Container used to run salt tests focusing on SUSE Manager use cases" > $DESTINATION/Dockerfile
echo "#" >> $DESTINATION/Dockerfile
echo "# NAME                  $CONTAINER_NAME" >> $DESTINATION/Dockerfile
echo "# VERSION               ?.?.?" >> $DESTINATION/Dockerfile


cat docker/Dockerfile.template | while read line; do echo $(eval echo `echo -e $line`); done >> $DESTINATION/Dockerfile
