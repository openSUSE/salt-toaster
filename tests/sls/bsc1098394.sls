{% set kiwi_dir = '/tmp/bsc1098394' %}

# repo for common kiwi build needs - mainly RPM with SUSE Manager certificate
{{ kiwi_dir }}/repo:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 755

{{ kiwi_dir }}/repo/rhn-org-trusted-ssl-cert-osimage-1.0-1.noarch.rpm:
  file.managed:
    - source: salt://rhn-org-trusted-ssl-cert-osimage-1.0-1.noarch.rpm
