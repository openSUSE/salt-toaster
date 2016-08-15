set -e

patch -d /salt/src/salt-devel/ -p1 -i ../0001-tserong-suse.com-We-don-t-have-python-systemd-so-not.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0002-Run-salt-master-as-dedicated-salt-user.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0003-Check-if-byte-strings-are-properly-encoded-in-UTF-8.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0004-do-not-generate-a-date-in-a-comment-to-prevent-rebui.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0005-Use-SHA256-hash-type-by-default.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0006-Add-SUSE-Manager-plugin.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0007-fix-salt-summary-to-count-not-responding-minions-cor.patch
patch -d /salt/src/salt-devel/ -p1 -i ../0008-Run-salt-api-as-user-salt-bsc-990029.patch
