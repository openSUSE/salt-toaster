test-patches-downloaded:
  pkg.installed:
    - downloadonly: True
    - patches:
{% for patch in pillar.get('patches', []) %}
      - {{ patch }}
{% endfor %}
