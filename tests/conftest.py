import pytest


@pytest.fixture(autouse=True)
def platform(request):
    configtags = set(request.config.getini('CONFIG_TAG'))

    platform_marker = request.node.get_marker('platform')
    platform_xfail_marker = request.node.get_marker('platform_xfail')

    if platform_marker:
        if configtags.isdisjoint(set(platform_marker.args)):
            pytest.skip('skipped on this configuration: {}'.format(configtags))
    elif platform_xfail_marker:
        if not configtags.isdisjoint(set(platform_xfail_marker.args)):
            request.node.add_marker(pytest.mark.xfail())
