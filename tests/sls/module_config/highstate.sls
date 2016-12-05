{% set postdata = data.get('post', {}) %}

salt-ssh:
  runner.ssh.cmd:
    - args:
        - {{ postdata.target }}
        - state.apply
    - kwargs:
        arg:
            - {{ postdata.os }}.{{ postdata.role }}
