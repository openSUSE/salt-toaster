oldest-version:
  pkg.installed:
    - name: test-package
    - version': 42:0.0-3.1

latest-version:
  pkg.latest:
    - name: test-package
    - require:
      - pkg: oldest-version
