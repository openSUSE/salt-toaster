set -e

zypper --non-interactive in salt-master salt-minion salt-proxy salt-ssh
zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive in git curl
zypper --non-interactive up zypper libzypp
