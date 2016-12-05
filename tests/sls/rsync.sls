rsyncpackage:
  pkg.installed:
    - name: rsync

/tmp:
    rsync.synchronized:
      - source: /salt-toaster/tests/data
      - force: True
