#!/bin/bash
set -e

# make sure the package repository is up to date
zypper --non-interactive --gpg-auto-import-keys ref

zypper -n in --no-recommends \
    python-devel \
    libgit2-devel \
    python-pytest

# required for unit tests install with recommends
zypper -n in quilt rpm-build
