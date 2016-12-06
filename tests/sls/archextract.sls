rsyncpackage:
  pkg.installed:
    - name: unzip

extract-zip-archive:
  archive.extracted:
    - name: /tmp/
    - source: /salt-toaster/tests/data/archive-sample.zip
    - archive_format: zip
    - overwrite: true
