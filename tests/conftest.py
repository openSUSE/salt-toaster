import pytest


@pytest.fixture(autouse=True)
def platform(request):
    marker = request.node.get_marker('platform')
    if marker:
        expected = marker.args[0]
        minion = request.getfuncargvalue('minion')
        platform = minion['container'].get_os_release()['ID']
        action = marker.kwargs.get('action', 'skip')
        if platform != expected and action == 'skip':
            pytest.skip('skipped on this platform: {}'.format(platform))
        elif platform == expected and action == 'xfail':
            request.node.add_marker(pytest.mark.xfail())