# -*- coding: utf-8 -*-
some-utf8-file-create:
  file.managed:
    - name: '/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt'
    - contents: \xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98
    - makedirs: True
    - replace: True
    - show_diff: True
some-utf8-file-create2:
  file.managed:
    - name: '/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt'
    - contents: |
       \xec\xb2\xab \xeb\xb2\x88\xec\xa7\xb8 \xed\x96\x89
       \xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98
       \xeb\xa7\x88\xec\xa7\x80\xeb\xa7\x89 \xed\x96\x89
    - replace: True
    - show_diff: True
some-utf8-file-exists:
  file.exists:
    - name: '/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt'
    - require:
      - file: some-utf8-file-create2
some-utf8-file-content-test:
  cmd.run:
    - name: \'cat "/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt"\'
    - require:
      - file: some-utf8-file-exists
some-utf8-file-content-remove:
  cmd.run:
    - name: \'rm -f "/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt"\'
    - require:
      - cmd: some-utf8-file-content-test
some-utf8-file-removed:
  file.missing:
    - name: '/tmp/salt-tests-tmpdir/salt_utf8_tests/\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xec\x8b\x9c\xed\x97\x98.txt'
    - require:
      - cmd: some-utf8-file-content-remove'
