#!/bin/bash
set -e

# make sure the package repository is up to date
zypper --non-interactive --gpg-auto-import-keys ref

# Packages required to run salt-minion
zypper -n in  --no-recommends iproute2 \
                              python \
                              cron \
                              sysconfig \
                              python-openssl \
                              postfix \
                              psmisc \
                              udev \
                              make \
                              python-mock \
                              python-pip \
                              python-pytest \
                              python-unittest2 \
                              python-salt-testing \
                              net-tools \
                              bind-utils

# required for unit tests install with recommends
zypper -n in quilt tar

zypper -n in vim less

zypper -n in python-devel
