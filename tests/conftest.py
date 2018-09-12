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
        pytest.logentries.append(self.format(report))  # pylint: disable=no-member


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
        for item in pytest.logentries:  # pylint: disable=no-member
            terminalreporter.write_line(item)
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        if not item.module.__name__ in pytest.logentries:  # pylint: disable=no-member
            logger.info(item.module.__name__)
        yield



@pytest.fixture(scope="session")
def docker_client():
    client = Client(base_url='unix://var/run/docker.sock', timeout=180)
    return client


@pytest.fixture(autouse=True)
def tagschecker(request):
    tags = set(request.config.getini('TAGS'))

    tags_marker = request.node.get_closest_marker('tags')
    xfailtags_marker = request.node.get_closest_marker('xfailtags')
    skiptags_marker = request.node.get_closest_marker('skiptags')

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


class SaltToasterException(Exception):
    pass

class ToasterTestsProfiling(object):
    """Toaster Tests Profiling plugin for pytest."""

    AVAILABLE_MODES = ['boolean', 'cumulative', "deltas"]

    global_profile = None
    mode = None
    metrics = {}

    def __init__(self, mode="default"):
        self.global_profile = cProfile.Profile()
        self.global_profile.enable()
        if mode in self.AVAILABLE_MODES:
            self.mode = mode
        else:
            raise SaltToasterException("Mode '{}' is not supported".format(mode))
        from_json = True if self.mode == "cumulative" else False
        self.metrics = self.read_initial_values(from_json=from_json)

    def read_initial_values(self, from_json=False):
        timings = {
            'pytest_runtest_setup': 0,
            'pytest_runtest_call': 0,
            'pytest_runtest_teardown': 0
        }
        if from_json:
            # Read possible values on the JSON file
            try:
                with open(TOASTER_TIMINGS_JSON) as infile:
                    timings.update(json.load(infile))
            except IOError as exc:
                logger.error("Failed to read JSON file: {}".format(exc))
        return timings

    def export_metrics_to_prometheus(self, metrics):
        # Export metrics to prometheus node exporter
        if self.mode == "boolean":
            metrics_header = \
'''
# HELP node_salt_toaster Pytest step being executed at the moment (1 = yes, 0 = no).
# TYPE node_salt_toaster gauge
'''
        else:
            metrics_header = \
'''
# HELP node_salt_toaster Seconds pytest spent in each Salt toaster step.
# TYPE node_salt_toaster counter
'''
        metrics_str = metrics_header + \
'''
node_salt_toaster{{step="pytest_runtest_setup"}} {pytest_runtest_setup}
node_salt_toaster{{step="pytest_runtest_call"}} {pytest_runtest_call}
node_salt_toaster{{step="pytest_runtest_teardown"}} {pytest_runtest_teardown}
'''
        try:
            with open(NODE_EXPORTER_METRIC_FILE, 'w') as metrics_file:
                metrics_file.write(
                    metrics_str.format(
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
        for item in self.metrics.keys():
            values[item] += self.metrics[item]
        with open(json_filename, 'w') as outfile:
            json.dump(values, outfile)
        self.export_metrics_to_prometheus(values)

    def export_metrics_delta(self, old_metrics, new_metrics, json_filename):
        deltas = {}
        for item in self.metrics.keys():
            deltas[item] = new_metrics[item] - old_metrics[item]
        with open(json_filename, 'w') as outfile:
            json.dump(new_metrics, outfile)
        self.metrics = new_metrics
        self.export_metrics_to_prometheus(deltas)

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
        if self.mode == "deltas":
            self.export_metrics_delta(self.metrics, timings, TOASTER_TIMINGS_JSON)
        elif self.mode == "cumulative":
            self.accumulate_values_to_json(timings, TOASTER_TIMINGS_JSON)

    def process_stats_switch_on(self, stepname):
        self.metrics[stepname] = 1
        self.export_metrics_to_prometheus(self.metrics)

    def process_stats_switch_off(self, stepname):
        self.metrics[stepname] = 0
        self.export_metrics_to_prometheus(self.metrics)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):  # @UnusedVariable
        if self.mode == "boolean":
            self.process_stats_switch_on("pytest_runtest_setup")
            yield
            self.process_stats_switch_off("pytest_runtest_setup")
        else:
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):  # @UnusedVariable
        if self.mode == "boolean":
            self.process_stats_switch_on("pytest_runtest_call")
            yield
            self.process_stats_switch_off("pytest_runtest_call")
        else:
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item, nextitem):  # @UnusedVariable
        if self.mode == "boolean":
            self.process_stats_switch_on("pytest_runtest_teardown")
            yield
            self.process_stats_switch_off("pytest_runtest_teardown")
        elif self.mode in ["cumulative", "deltas"]:
            yield
            self.process_stats()
        else:
            yield

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
    plugin = ExtraSaltPlugin()
    config.pluginmanager.register(plugin, 'ExtraSaltPlugin')
    config.pluginmanager.register(ToasterTestsProfiling(mode="boolean"))
