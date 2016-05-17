systemsmanagement_saltstack:
  pkgrepo.managed:
    - url: {{ REPO_URL }}
    - enabled: True
    - refresh: True
    - gpgkey: {{ GPGKEY_URL }}
