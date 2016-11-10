include:
  - latest
latest-version-again:
  pkg.latest:
    - name: test-package
    - require:
      - pkg: latest-version
