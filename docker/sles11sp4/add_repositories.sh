#!/bin/bash
set -e

# Use your credentials for the 'nu.novell' domain within the URL, in case required
zypper ar -f 'http://nu.novell.com/repo/$RCE/SLES11-SP4-Pool/sle-11-x86_64/' "SLES11 SP4 Pool"
zypper ar -f 'http://nu.novell.com/repo/$RCE/SLES11-SP4-Updates/sle-11-x86_64/' "SLES11 SP4 Updates"
zypper ar -f 'http://nu.novell.com/repo/$RCE/SLE11-SDK-SP4-Pool/sle-11-x86_64' "SLE-SDK11 SP4 Pool"
zypper ar -f 'http://nu.novell.com/repo/$RCE/SLE11-SDK-SP4-Updates/sle-11-x86_64' "SLE-SDK11 SP4 Updates"

zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack/SLE_11_SP4/ "salt"
zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/testing/SLE_11_SP4/ "salt_testing"
zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/testing:/testpackages/SLE_11_SP4/ "testpackages"

zypper mr -p 98 salt_testing
zypper mr -p 98 testpackages
