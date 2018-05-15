{% set pattern = grains['saltversion'] %}
{% set installed = salt['cmd.shell']('rpm -q --last salt | head -1 | cut -f1 -d " "') | replace('salt-', '') %}

reboot:
  cmd.run:
    - name: "echo 'shutdown'"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ pattern }}"
    - failhard: True
    - fire_event: True
