import salt.utils.process


def test_systemd_notify_by_socket():
    salt.utils.process.notify_systemd()
