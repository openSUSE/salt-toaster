{% set pattern = "^pattern$" %}
{% set installed = salt['cmd.shell']('echo my new-pattern is great | head -1 | cut -f2 -d " "') | replace('new-', '') %}

reboot:
  cmd.run:
    - name: "echo 'shutdown'"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ pattern }}"
    - failhard: True
    - fire_event: True
