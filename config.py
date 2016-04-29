TIME_LIMIT = 30
SALT_MASTER_START_CMD = "salt-master -c {SALT_ROOT}"
SALT_MINION_START_CMD = "salt-minion -l debug -c {SALT_ROOT}"
SALT_KEY_CMD = "salt-key -c {SALT_ROOT}"
SALT_CALL = "salt -l debug -c {SALT_ROOT} {HOSTNAME}"
