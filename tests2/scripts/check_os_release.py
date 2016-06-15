import os
import json

if __name__ == '__main__':
    print(json.dumps({
        'exists': os.path.isfile('/etc/os-release')
    }))
