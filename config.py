TIME_LIMIT = 120
SALT_MASTER_START_CMD = "salt-master -c {SALT_ROOT}"
SALT_MINION_START_CMD = "salt-minion -l debug -c {SALT_ROOT}"
SALT_PROXYMINION_START_CMD = "salt-proxy -l debug -c {SALT_ROOT} --proxyid={PROXY_ID}"
SALT_KEY_CMD = "salt-key -c {SALT_ROOT} --output json"
SALT_CALL = "salt -l debug -c {SALT_ROOT} {HOSTNAME}"
SALT_PROXY_CALL = "salt -l debug -c {SALT_ROOT} {PROXY_ID} --output json"
START_PROXY_SERVER = "python -m tests.proxy_server {PROXY_SERVER_PORT}"
WHEEL_CONFIG = dict(user='apiuser', password='linux')
