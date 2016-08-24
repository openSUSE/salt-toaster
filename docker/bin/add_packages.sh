#!/bin/sh
set -e

# make sure the package repository is up to date
zypper --non-interactive --gpg-auto-import-keys ref

zypper -n in --no-recommends python-devel python-pip make bind-utils
pip install pytest mock==1.0.0 timelib
