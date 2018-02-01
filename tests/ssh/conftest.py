import pytest
from saltcontainers.factories import ContainerFactory


@pytest.fixture(scope='module')
def module_config(request, container):
    return {
        "masters": [
            {
                "config": {
                    "container__config__salt_config__extra_configs": {
                        "thin_extra_mods": {
                            "thin_extra_mods": "msgpack"
                        },
                        "custom_tops": {
                            "extension_modules": "/salt-toaster/tests/sls/ssh/xmod",
                            "master_tops": {
                                "toptest": True
                            },
                        },
                    },
                    "container__config__salt_config__apply_states": {
                        "top": "tests/sls/ssh/top.sls",
                        "ssh": "tests/sls/ssh/ssh.sls"
                    },
                    "container__config__salt_config__roster": [container]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def container(request, salt_root):
    obj = ContainerFactory(
        config__image=request.config.getini('MINION_IMAGE') or request.config.getini('IMAGE'),
        config__salt_config=None,
        ssh_config={'user': 'root', 'password': 'admin123'})
    obj.run('zypper --non-interactive rm salt')  # Remove salt from the image!!
    request.addfinalizer(obj.remove)
    return obj
