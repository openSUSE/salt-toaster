test-patches-downloaded:
  pkg.patch_downloaded:
    - advisory_ids:
{% for patch in pillar.get('patches', []) %}
      - {{ patch }}
{% endfor %}
