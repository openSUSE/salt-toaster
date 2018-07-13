import cProfile
import json
import pstats
import pytest
import logging
import StringIO
import re
from docker import Client


PROFILE_RESULTS_FILE = 'reports/global.prof'
TOASTER_TIMINGS_JSON = '/tmp/toaster-timings.json'
NODE_EXPORTER_METRIC_FILE = '/var/lib/node_exporter/textfile_collector/salt_toaster.prom'


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

    global_profile = None
    initial_metrics = {}

    def __init__(self):
        self.global_profile = cProfile.Profile()
        self.global_profile.enable()
        self.initial_metrics = self.read_values_from_json(TOASTER_TIMINGS_JSON)

    def read_values_from_json(self, json_filename):
        timings = {
            'pytest_runtest_setup': 0,
            'pytest_runtest_call': 0,
            'pytest_runtest_teardown': 0
        }
        # Read possible values on the JSON file
        try:
            with open(json_filename) as infile:
                timings.update(json.load(infile))
                return timings
        except IOError:
            return timings

    def export_metrics_to_prometheus(self, metrics):
        # Export metrics to prometheus node exporter
        try:
            with open(NODE_EXPORTER_METRIC_FILE, 'w') as metric_file:
                metric_str = \
'''
# HELP node_salt_toaster Seconds pytest spent in each Salt toaster step.
# TYPE node_salt_toaster counter
node_salt_toaster{{step="pytest_runtest_setup"}} {pytest_runtest_setup}
node_salt_toaster{{step="pytest_runtest_call"}} {pytest_runtest_call}
node_salt_toaster{{step="pytest_runtest_teardown"}} {pytest_runtest_teardown}
'''
                metric_file.write(
                    metric_str.format(
                        pytest_runtest_setup=metrics['pytest_runtest_setup'],
                        pytest_runtest_call=metrics['pytest_runtest_call'],
                        pytest_runtest_teardown=metrics['pytest_runtest_teardown'],
                    ).lstrip()
                )
        except IOError as exc:
            logger.error("Failed to export metrics to Prometheus node " \
                "exporter file {}: {}".format(NODE_EXPORTER_METRIC_FILE, exc))

    def accumulate_values_to_json(self, values, json_filename):
        # Accumulate current values with the initial ones
        for item in self.initial_metrics.keys():
            values[item] += self.initial_metrics[item]
        with open(json_filename, 'w') as outfile:
            json.dump(values, outfile)
        self.export_metrics_to_prometheus(values)

    def process_stats(self):  # @UnusedVariable
        timings = {
            'pytest_runtest_setup': 0,
            'pytest_runtest_call': 0,
            'pytest_runtest_teardown': 0
        }
        self.global_profile.disable()
        self.global_profile.dump_stats(PROFILE_RESULTS_FILE)
        self.global_profile.enable()
        stream = StringIO.StringIO()
        stats = pstats.Stats(PROFILE_RESULTS_FILE, stream=stream)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_setup', 1)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_call', 1)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_teardown', 1)
        for line in stream.getvalue().split('\n'):
            if re.match('.+\d+.+\d+\.\d+.+\d+\.\d+.+\d+\.\d+.+\d+\.\d+.*', line):
                line_list = [item for item in line.split(' ') if item]
                if 'pytest_runtest_setup' in line:
                   timings['pytest_runtest_setup'] = float(line_list[3])
                elif 'pytest_runtest_call' in line:
                   timings['pytest_runtest_call'] = float(line_list[3])
                elif 'pytest_runtest_teardown' in line:
                   timings['pytest_runtest_teardown'] = float(line_list[3])
        self.accumulate_values_to_json(timings, TOASTER_TIMINGS_JSON)

    def pytest_runtest_teardown(self, item, nextitem):  # @UnusedVariable
        self.process_stats()

    def pytest_terminal_summary(self, terminalreporter):
        self.global_profile.disable()
        self.global_profile.dump_stats(PROFILE_RESULTS_FILE)
        terminalreporter.write_sep("-",
            "generated cProfile stats file on: {}".format(PROFILE_RESULTS_FILE))
        terminalreporter.write_sep("-", "Salt Toaster Profiling Stats")
        stats = pstats.Stats(self.global_profile, stream=terminalreporter)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_setup', 1)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_call', 1)
        stats.sort_stats('cumulative').print_stats('pytest_runtest_teardown', 1)


def pytest_configure(config):
    """pytest_configure hook for profiling plugin"""
    config.pluginmanager.register(ToasterTestsProfiling())
