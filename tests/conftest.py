import pytest


@pytest.fixture(autouse=True)
def tagschecker(request):
    tags = set(request.config.getini('TAGS'))

    platform_marker = request.node.get_marker('tags')
    platform_xfail_marker = request.node.get_marker('tags_xfail')

    if platform_marker:
        if tags.isdisjoint(set(platform_marker.args)):
            pytest.skip('skipped on this configuration: {}'.format(tags))
    elif platform_xfail_marker:
        if not tags.isdisjoint(set(platform_xfail_marker.args)):
            request.node.add_marker(pytest.mark.xfail())
