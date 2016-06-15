import salt.config
import salt.wheel
import json
from config import WHEEL_CONFIG

if __name__ == '__main__':
    opts = salt.config.master_config('/etc/salt/master')
    wheel_client = salt.wheel.WheelClient(opts)
    output = wheel_client.cmd_sync(
        dict(
            fun='config.values',
            eauth="pam",
            username=WHEEL_CONFIG['user'],
            password=WHEEL_CONFIG['password']
        )
    )
    print(json.dumps(output))
