packages:
  pkg.installed:
    - pkgs:
      - salt-api


salt-api:
  cmd.run:
    - name: salt-api -d -l debug
    - unless: pgrep salt-api
    - require:
      - pkg: packages
