set -e

zypper --non-interactive in salt-master salt-minion salt-proxy
zypper --non-interactive in --oldpackage test-package=42:0.0
zypper --non-interactive up zypper libzypp
