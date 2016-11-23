salt-api:
 pkgrepo.managed:
   - baseurl: http://download.opensuse.org/repositories/systemsmanagement:/saltstack/SLE_12_SP1/
   - name: saltstack
   - refresh: True

 pkg.installed:
   - pkgs:
     - salt-api

 cmd.run:
   - name: salt-api -d -l debug
