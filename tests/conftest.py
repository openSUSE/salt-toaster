import pytest


@pytest.fixture(scope='module')
def platform(minion):
    return minion['container'].get_os_release()['ID']


@pytest.fixture()
def platform_required(request):
    marker = request.node.get_marker('platform')
    if marker:
        expected_platform = marker.args[0]
        actual_platform = request.getfuncargvalue('platform')
        action = marker.kwargs.get('action', 'skip')
        if actual_platform != expected_platform and action == 'skip':
            pytest.skip('skipped on this platform: {}'.format(platform))
        elif action == 'xfail':
            request.node.add_marker(pytest.mark.xfail())
