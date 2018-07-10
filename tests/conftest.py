import cProfile
import json
import pstats
import pytest
import logging
import StringIO
import re
from docker import Client


PROFILE_RESULTS_FILE = 'reports/global.prof'
TOASTER_TIMINGS_JSON = 'reports/toaster-timings.json'


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


class ToasterTestsProfiling(object):
    """Toaster Tests Profiling plugin for pytest."""
    tests_profs = []
    docker_profs = []
    global_profile = None

    def __init__(self):
        self.global_profile = cProfile.Profile()
        self.global_profile.enable()

    def accumulate_values_to_json(self, values, json_filename):
        output = {}
        # Read possible values on the file
        try:
            with open(json_filename) as infile:
                output = json.load(infile)
        except IOError:
            pass

        # Accumulate current values with older ones
        for item in output.keys():
            values[item] += output[item]

        with open(json_filename, 'w') as outfile:
            json.dump(values, outfile)

    def pytest_terminal_summary(self, terminalreporter):
        self.global_profile.disable()
        self.global_profile.dump_stats(PROFILE_RESULTS_FILE)
        terminalreporter.write("--------------------- Salt Toaster Profiling Stats ---------------------\n")
        stats = pstats.Stats(self.global_profile, stream=terminalreporter)
        stats.sort_stats('cumulative').print_stats('runtest_setup', 1)
        stats.sort_stats('cumulative').print_stats('runtest_call', 1)
        stats.sort_stats('cumulative').print_stats('runtest_teardown', 1)

    def pytest_sessionfinish(self, session):  # @UnusedVariable
        timings = {
            'runtest_setup_value': 0,
            'runtest_call_value': 0,
            'runtest_teardown_value': 0
        }
        stream = StringIO.StringIO()
        stats = pstats.Stats(PROFILE_RESULTS_FILE, stream=stream)
        stats.sort_stats('cumulative').print_stats('runtest_setup', 1)
        stats.sort_stats('cumulative').print_stats('runtest_call', 1)
        stats.sort_stats('cumulative').print_stats('runtest_teardown', 1)
        for line in stream.getvalue().split('\n'):
            if re.match('.+\d+.+\d+\.\d+.+\d+\.\d+.+\d+\.\d+.+\d\.\d+.*', line):
                line_list = [item for item in line.split(' ') if item]
                if 'runtest_setup' in line:
                   timings['runtest_setup_value'] = float(line_list[3])
                elif 'runtest_call' in line:
                   timings['runtest_call_value'] = float(line_list[3])
                elif 'runtest_teardown' in line:
                   timings['runtest_teardown_value'] = float(line_list[3])
        self.accumulate_values_to_json(timings, TOASTER_TIMINGS_JSON)


def pytest_configure(config):
    """pytest_configure hook for profiling plugin"""
    config.pluginmanager.register(ToasterTestsProfiling())
