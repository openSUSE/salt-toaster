#!/bin/bash
set -e

# Use your credentials for the 'nu.novell' domain within the URL, in case required
zypper ar -f http://nu.novell.com/SUSE/Products/SLE-SERVER/12-SP1/x86_64/product/ "SLES 12 SP1 Pool"
zypper ar -f http://nu.novell.com/SUSE/Updates/SLE-SERVER/12-SP1/x86_64/update/ "SLES 12 SP1 Updates"
zypper ar -f http://nu.novell.com/SUSE/Products/SLE-SDK/12-SP1/x86_64/product/ "SLE-SDK 12 SP1 Pool"
zypper ar -f http://nu.novell.com/SUSE/Updates/SLE-SDK/12-SP1/x86_64/update/ "SLE-SDK 12 SP1 Updates"
zypper ar -f http://nu.novell.com/SUSE/Products/SLE-Module-Public-Cloud/12/x86_64/product/ "SLE-Module-Public-Cloud 12 Pool"
zypper ar -f http://nu.novell.com/SUSE/Updates/SLE-Module-Public-Cloud/12/x86_64/update/ "SLE-Module-Public-Cloud 12 Updates"

zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack/SLE_12/ "salt"
zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/testing/SLE_12/ "salt_testing"
zypper ar -f http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/testing:/testpackages/SLE_12/ "testpackages"

zypper mr -p 98 salt_testing
zypper mr -p 98 testpackages
