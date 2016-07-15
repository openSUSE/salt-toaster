import pytest


@pytest.fixture(autouse=True)
def tagschecker(request):
    tags = set(request.config.getini('TAGS'))

    tags_marker = request.node.get_marker('tags')
    xfailtags_marker = request.node.get_marker('xfailtags')
    skiptags_marker = request.node.get_marker('skiptags')

    if tags_marker and tags.isdisjoint(set(tags_marker.args)):
            pytest.skip('skipped for this tags: {}'.format(tags))
    elif skiptags_marker and not tags.isdisjoint(set(skiptags_marker.args)):
            pytest.skip('skipped for this tags: {}'.format(tags))
    elif xfailtags_marker and not tags.isdisjoint(set(xfailtags_marker.args)):
            request.node.add_marker(pytest.mark.xfail())
