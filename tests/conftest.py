import pytest
from docker import Client


@pytest.fixture(scope="session")
def docker_client():
    client = Client(base_url='unix://var/run/docker.sock', timeout=180)
    return client


@pytest.fixture(autouse=True)
def tagschecker(request):
    tags = set(request.config.getini('TAGS'))

    tags_marker = request.node.get_marker('tags')
    xfailtags_marker = request.node.get_marker('xfailtags')
    skiptags_marker = request.node.get_marker('skiptags')

    if xfailtags_marker and not tags.isdisjoint(set(xfailtags_marker.args)):
        request.node.add_marker(pytest.mark.xfail())
    elif (
        tags_marker and tags.isdisjoint(set(tags_marker.args)) or
        skiptags_marker and not tags.isdisjoint(set(skiptags_marker.args))
    ):
        pytest.skip('skipped for this tags: {}'.format(tags))
