sle-sdk-pool:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Products/SLE-SDK/12-SP1/x86_64/product/
    - name: SLE-SDK 12 SP1 Pool
    - refresh: True

sle-sdk-updates:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Updates/SLE-SDK/12-SP1/x86_64/update/
    - name: SLE-SDK 12 SP1 Updates
    - refresh: True

sle-module-public-cloud-12-pool:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Products/SLE-Module-Public-Cloud/12/x86_64/product/
    - name: SLE-Module-Public-Cloud 12 Pool
    - refresh: True

sle-module-public-cloud-12-updates:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Updates/SLE-Module-Public-Cloud/12/x86_64/update/
    - name: SLE-Module-Public-Cloud 12 Updates
    - refresh: True

sle-manager-tools-12-pool:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Products/SLE-Manager-Tools/12/x86_64/product/
    - name: SLE-Manager-Tools 12 Pool
    - refresh: True

sle-manager-tools-12-updates:
  pkgrepo.managed:
    - baseurl: http://nu.novell.com/SUSE/Updates/SLE-Manager-Tools/12/x86_64/update/
    - name: SLE-Manager-Tools 12 Updates
    - refresh: True

testpackages:
  pkgrepo.managed:
    - baseurl: http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/testing:/testpackages/SLE_12_SP1/
    - gpgcheck: 0
    - name: "testpackages"
    - refresh: True

salt:
  pkgrepo.managed:
    - baseurl: http://download.opensuse.org/repositories/systemsmanagement:/saltstack:/products/SLE_12_SP1/
    - gpgcheck: 0
    - name: salt
    - priority: 1
    - refresh: True


packages:
  pkg.installed:
    - gpgautoimport: True
    - pkgs:
      - salt-master
      - netcat-openbsd
      - vim
      - python-pip
    - require:
      - pkgrepo: sle-sdk-pool
      - pkgrepo: sle-sdk-updates
      - pkgrepo: sle-module-public-cloud-12-pool
      - pkgrepo: sle-module-public-cloud-12-updates
      - pkgrepo: sle-manager-tools-12-pool
      - pkgrepo: sle-manager-tools-12-updates
      - pkgrepo: testpackages
      - pkgrepo: salt

pippack:
  pip.installed:
    - pkgs:
      - rpdb
    - require:
      - pkg: packages


salt-master:
  cmd.run:
    - name: salt-master -d -l debug
    - unless: pgrep salt-master
    - require:
      - pkg: packages
