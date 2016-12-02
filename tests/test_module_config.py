import pytest
from saltcontainers.factories import MasterFactory


# @pytest.fixture(scope='module')
# def module_config(request, controller):
#     return {
#         'containers': [
#             {
#                 'config': {
#                     "container__config__salt_config__apply_states": {
#                         "top": "tests/sls/module_config/top.sls",
#                         "setup": "tests/sls/module_config/setup.sls"
#                     },
#                 }
#             }
#         ]
#     }


@pytest.fixture(scope='session')
def controller(request, docker_client, salt_root):
    controller = MasterFactory(
        container__config__docker_client=docker_client,
        container__config__image='registry.mgr.suse.de/toaster-sles12sp1-products',
        container__config__salt_config__tmpdir=salt_root,
        container__config__salt_config__apply_states={
            "top": "tests/sls/module_config/top.sls",
            "setup": "tests/sls/module_config/setup.sls"})
    request.addfinalizer(controller['container'].remove)
    return controller


def test_pkg_latest_version(controller):
    import pdb; pdb.set_trace()
