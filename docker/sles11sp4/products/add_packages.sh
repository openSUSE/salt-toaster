#!/bin/bash
set -e

zypper -n in  --no-recommends python-pytest

zypper -n in python-devel
