import pytest
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Handler(logging.Handler):

    def emit(self, report):
        pytest.logentries.append(self.format(report))


class ExtraSaltPlugin(object):

    @pytest.hookimpl()
    def pytest_namespace(self):
        return dict(logentries=[])

    @pytest.hookimpl(hookwrapper=True)
    def pytest_sessionstart(self, session):
        handler = Handler()
        logging.root.addHandler(handler)
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_terminal_summary(self, terminalreporter):
        for item in pytest.logentries:
            terminalreporter.write_line(item)
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        if not item.module.__name__ in pytest.logentries:
            logger.info(item.module.__name__)
        yield


def pytest_configure(config):
    plugin = ExtraSaltPlugin()
    config.pluginmanager.register(plugin, 'ExtraSaltPlugin')


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


@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [
            {
                "minions": [
                    {
                        "config": {
                            "container__config__image": (
                                request.config.getini('MINION_IMAGE') or
                                request.config.getini('IMAGE')
                            )
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture(scope="module")
def master(setup):
    config, initconfig = setup
    return config['masters'][0]['fixture']


@pytest.fixture(scope="module")
def minion(setup):
    config, initconfig = setup
    minions = config['masters'][0]['minions']
    return minions[0]['fixture'] if minions else None
