"""
    :codeauthor: Pedro Algarvio (pedro@algarvio.me)

    tests.conftest
    ~~~~~~~~~~~~~~

    Prepare py.test for our test suite
"""
# pylint: disable=wrong-import-order,wrong-import-position,3rd-party-local-module-not-gated
# pylint: disable=redefined-outer-name,invalid-name,3rd-party-module-not-gated


import logging
import os
import pathlib
import pprint
import re
import shutil
import ssl
import stat
import sys
from functools import partial, wraps

import _pytest.logging
import _pytest.skipping
import psutil
import pytest
import salt._logging.impl
import salt.config
import salt.loader
import salt.log.mixins
import salt.utils.files
import salt.utils.path
import salt.utils.platform
import salt.utils.win_functions
from salt.serializers import yaml
from salt.utils.immutabletypes import freeze
from tests.support.helpers import (
    PRE_PYTEST_SKIP_OR_NOT,
    PRE_PYTEST_SKIP_REASON,
    Webserver,
    get_virtualenv_binary_path,
)
from tests.support.pytest.helpers import *  # pylint: disable=unused-wildcard-import
from tests.support.runtests import RUNTIME_VARS
from tests.support.sminion import check_required_sminion_attributes, create_sminion
#
# Toaster specifics
from fnmatch import fnmatch


TESTS_DIR = pathlib.Path.cwd() / "tests"
PYTESTS_DIR = TESTS_DIR / "pytests"
CODE_DIR = TESTS_DIR.parent

# Change to code checkout directory
os.chdir(str(CODE_DIR))

# Make sure the current directory is the first item in sys.path
if str(CODE_DIR) in sys.path:
    sys.path.remove(str(CODE_DIR))
sys.path.insert(0, str(CODE_DIR))

# Coverage
if "COVERAGE_PROCESS_START" in os.environ:
    MAYBE_RUN_COVERAGE = True
    COVERAGERC_FILE = os.environ["COVERAGE_PROCESS_START"]
else:
    COVERAGERC_FILE = str(CODE_DIR / ".coveragerc")
    MAYBE_RUN_COVERAGE = (
        sys.argv[0].endswith("pytest.py") or "_COVERAGE_RCFILE" in os.environ
    )
    if MAYBE_RUN_COVERAGE:
        # Flag coverage to track suprocesses by pointing it to the right .coveragerc file
        os.environ["COVERAGE_PROCESS_START"] = str(COVERAGERC_FILE)

# Define the pytest plugins we rely on
pytest_plugins = ["tempdir", "helpers_namespace"]

# Define where not to collect tests from
collect_ignore = ["setup.py"]


# Patch PyTest logging handlers
class LogCaptureHandler(
    salt.log.mixins.ExcInfoOnLogLevelFormatMixIn, _pytest.logging.LogCaptureHandler
):
    """
    Subclassing PyTest's LogCaptureHandler in order to add the
    exc_info_on_loglevel functionality and actually make it a NullHandler,
    it's only used to print log messages emmited during tests, which we
    have explicitly disabled in pytest.ini
    """


_pytest.logging.LogCaptureHandler = LogCaptureHandler


class LiveLoggingStreamHandler(
    salt.log.mixins.ExcInfoOnLogLevelFormatMixIn,
    _pytest.logging._LiveLoggingStreamHandler,
):
    """
    Subclassing PyTest's LiveLoggingStreamHandler in order to add the
    exc_info_on_loglevel functionality.
    """


_pytest.logging._LiveLoggingStreamHandler = LiveLoggingStreamHandler

# Reset logging root handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)


# Reset the root logger to its default level(because salt changed it)
logging.root.setLevel(logging.WARNING)

log = logging.getLogger("salt.testsuite")


# ----- PyTest Tempdir Plugin Hooks --------------------------------------------------------------------------------->
def pytest_tempdir_basename():
    """
    Return the temporary directory basename for the salt test suite.
    """
    return "stsuite"


# <---- PyTest Tempdir Plugin Hooks ----------------------------------------------------------------------------------


# ----- CLI Options Setup ------------------------------------------------------------------------------------------->
def pytest_addoption(parser):
    """
    register argparse-style options and ini-style config values.
    """
    test_selection_group = parser.getgroup("Tests Selection")
    test_selection_group.addoption(
        "--from-filenames",
        default=None,
        help=(
            "Pass a comma-separated list of file paths, and any test module which"
            " corresponds to the specified file(s) will run. For example, if 'setup.py'"
            " was passed, then the corresponding test files defined in"
            " 'tests/filename_map.yml' would run. Absolute paths are assumed to be"
            " files containing relative paths, one per line. Providing the paths in a"
            " file can help get around shell character limits when the list of files is"
            " long."
        ),
    )
    # Add deprecated CLI flag until we completely switch to PyTest
    test_selection_group.addoption(
        "--names-file", default=None, help="Deprecated option"
    )
    test_selection_group.addoption(
        "--transport",
        default="zeromq",
        choices=("zeromq", "tcp"),
        help=(
            "Select which transport to run the integration tests with, zeromq or tcp."
            " Default: %(default)s"
        ),
    )
    test_selection_group.addoption(
        "--ssh",
        "--ssh-tests",
        dest="ssh",
        action="store_true",
        default=False,
        help=(
            "Run salt-ssh tests. These tests will spin up a temporary "
            "SSH server on your machine. In certain environments, this "
            "may be insecure! Default: False"
        ),
    )
    test_selection_group.addoption(
        "--proxy",
        "--proxy-tests",
        dest="proxy",
        action="store_true",
        default=False,
        help="Run proxy tests (DEPRECATED)",
    )
    test_selection_group.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests.",
    )

    output_options_group = parser.getgroup("Output Options")
    output_options_group.addoption(
        "--output-columns",
        default=80,
        type=int,
        help="Number of maximum columns to use on the output",
    )
    output_options_group.addoption(
        "--no-colors",
        "--no-colours",
        default=False,
        action="store_true",
        help="Disable colour printing.",
    )

    # ----- Test Groups --------------------------------------------------------------------------------------------->
    # This will allow running the tests in chunks
    test_selection_group.addoption(
        "--test-group-count",
        dest="test-group-count",
        type=int,
        help="The number of groups to split the tests into",
    )
    test_selection_group.addoption(
        "--test-group",
        dest="test-group",
        type=int,
        help="The group of tests that should be executed",
    )
    # <---- Test Groups ----------------------------------------------------------------------------------------------
    # Toaster specific
    parser.addini("tests_type", help="Type of the tests being run", default='unit')


# <---- CLI Options Setup --------------------------------------------------------------------------------------------


# ----- Register Markers -------------------------------------------------------------------------------------------->
@pytest.mark.trylast
def pytest_configure(config):
    """
    called after command line options have been parsed
    and all plugins and initial conftest files been loaded.
    """
    for dirname in CODE_DIR.iterdir():
        if not dirname.is_dir():
            continue
        if dirname != TESTS_DIR:
            config.addinivalue_line("norecursedirs", str(CODE_DIR / dirname))

    # Expose the markers we use to pytest CLI
    config.addinivalue_line(
        "markers",
        "requires_salt_modules(*required_module_names): Skip if at least one module is"
        " not available.",
    )
    config.addinivalue_line(
        "markers",
        "requires_salt_states(*required_state_names): Skip if at least one state module"
        " is not available.",
    )
    config.addinivalue_line(
        "markers", "windows_whitelisted: Mark test as whitelisted to run under Windows"
    )
    config.addinivalue_line(
        "markers", "requires_sshd_server: Mark test that require an SSH server running"
    )
    config.addinivalue_line(
        "markers",
        "slow_test: Mark test as being slow. These tests are skipped by default unless"
        " `--run-slow` is passed",
    )
    # "Flag" the slowTest decorator if we're skipping slow tests or not
    os.environ["SLOW_TESTS"] = str(config.getoption("--run-slow"))

    # Toaster specific
    config.salt_version = salt.version.__version__
    config.xfail_list = get_list(config, 'xfail_list')
    config.ignore_list = get_list(config, 'ignore_list')


# <---- Register Markers ---------------------------------------------------------------------------------------------


# ----- PyTest Tweaks ----------------------------------------------------------------------------------------------->
def set_max_open_files_limits(min_soft=3072, min_hard=4096):

    # Get current limits
    if salt.utils.platform.is_windows():
        import win32file

        prev_hard = win32file._getmaxstdio()
        prev_soft = 512
    else:
        import resource

        prev_soft, prev_hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    # Check minimum required limits
    set_limits = False
    if prev_soft < min_soft:
        soft = min_soft
        set_limits = True
    else:
        soft = prev_soft

    if prev_hard < min_hard:
        hard = min_hard
        set_limits = True
    else:
        hard = prev_hard

    # Increase limits
    if set_limits:
        log.debug(
            " * Max open files settings is too low (soft: %s, hard: %s) for running the"
            " tests. Trying to raise the limits to soft: %s, hard: %s",
            prev_soft,
            prev_hard,
            soft,
            hard,
        )
        try:
            if salt.utils.platform.is_windows():
                hard = 2048 if hard > 2048 else hard
                win32file._setmaxstdio(hard)
            else:
                resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
        except Exception as err:  # pylint: disable=broad-except
            log.error(
                "Failed to raise the max open files settings -> %s. Please issue the"
                " following command on your console: 'ulimit -u %s'",
                err,
                soft,
            )
            exit(1)
    return soft, hard


def pytest_report_header():
    soft, hard = set_max_open_files_limits()
    return "max open files; soft: {}; hard: {}".format(soft, hard)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_collection_modifyitems(config, items):
    """
    called after collection has been performed, may filter or re-order
    the items in-place.

    :param _pytest.main.Session session: the pytest session object
    :param _pytest.config.Config config: pytest config object
    :param List[_pytest.nodes.Item] items: list of item objects
    """
    # Let PyTest or other plugins handle the initial collection
    yield
    groups_collection_modifyitems(config, items)
    from_filenames_collection_modifyitems(config, items)

    log.warning("Mofifying collected tests to keep track of fixture usage")
    for item in items:
        for fixture in item.fixturenames:
            if fixture not in item._fixtureinfo.name2fixturedefs:
                continue
            for fixturedef in item._fixtureinfo.name2fixturedefs[fixture]:
                if fixturedef.scope != "package":
                    continue
                try:
                    fixturedef.finish.__wrapped__
                except AttributeError:
                    original_func = fixturedef.finish

                    def wrapper(func, fixturedef):
                        @wraps(func)
                        def wrapped(self, request, nextitem=False):
                            try:
                                return self._finished
                            except AttributeError:
                                if nextitem:
                                    fpath = pathlib.Path(self.baseid).resolve()
                                    tpath = pathlib.Path(
                                        nextitem.fspath.strpath
                                    ).resolve()
                                    try:
                                        tpath.relative_to(fpath)
                                        # The test module is within the same package that the fixture is
                                        if (
                                            not request.session.shouldfail
                                            and not request.session.shouldstop
                                        ):
                                            log.debug(
                                                "The next test item is still under the"
                                                " fixture package path. Not"
                                                " terminating %s",
                                                self,
                                            )
                                            return
                                    except ValueError:
                                        pass
                                log.debug("Finish called on %s", self)
                                try:
                                    return func(request)
                                except BaseException as exc:  # pylint: disable=broad-except
                                    pytest.fail(
                                        "Failed to run finish() on {}: {}".format(
                                            fixturedef, exc
                                        ),
                                        pytrace=True,
                                    )
                                finally:
                                    self._finished = True

                        return partial(wrapped, fixturedef)

                    fixturedef.finish = wrapper(fixturedef.finish, fixturedef)
                    try:
                        fixturedef.finish.__wrapped__
                    except AttributeError:
                        fixturedef.finish.__wrapped__ = original_func


@pytest.hookimpl(trylast=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """
    implements the runtest_setup/call/teardown protocol for
    the given test item, including capturing exceptions and calling
    reporting hooks.

    :arg item: test item for which the runtest protocol is performed.

    :arg nextitem: the scheduled-to-be-next test item (or None if this
                   is the end my friend).  This argument is passed on to
                   :py:func:`pytest_runtest_teardown`.

    :return boolean: True if no further hook implementations should be invoked.


    Stops at first non-None result, see :ref:`firstresult`
    """
    request = item._request
    used_fixture_defs = []
    for fixture in item.fixturenames:
        if fixture not in item._fixtureinfo.name2fixturedefs:
            continue
        for fixturedef in reversed(item._fixtureinfo.name2fixturedefs[fixture]):
            if fixturedef.scope != "package":
                continue
            used_fixture_defs.append(fixturedef)
    try:
        # Run the test
        yield
    finally:
        for fixturedef in used_fixture_defs:
            fixturedef.finish(request, nextitem=nextitem)
    del request
    del used_fixture_defs


# <---- PyTest Tweaks ------------------------------------------------------------------------------------------------


# ----- Test Setup -------------------------------------------------------------------------------------------------->
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Fixtures injection based on markers or test skips based on CLI arguments
    """
    integration_utils_tests_path = str(TESTS_DIR / "integration" / "utils")
    if (
        str(item.fspath).startswith(integration_utils_tests_path)
        and PRE_PYTEST_SKIP_OR_NOT is True
    ):
        item._skipped_by_mark = True
        pytest.skip(PRE_PYTEST_SKIP_REASON)

    if item.get_closest_marker("slow_test"):
        if item.config.getoption("--run-slow") is False:
            item._skipped_by_mark = True
            pytest.skip("Slow tests are disabled!")

    requires_sshd_server_marker = item.get_closest_marker("requires_sshd_server")
    if requires_sshd_server_marker is not None:
        if not item.config.getoption("--ssh-tests"):
            item._skipped_by_mark = True
            pytest.skip("SSH tests are disabled, pass '--ssh-tests' to enable them.")
        item.fixturenames.append("sshd_server")
        item.fixturenames.append("salt_ssh_roster_file")

    requires_salt_modules_marker = item.get_closest_marker("requires_salt_modules")
    if requires_salt_modules_marker is not None:
        required_salt_modules = requires_salt_modules_marker.args
        if len(required_salt_modules) == 1 and isinstance(
            required_salt_modules[0], (list, tuple, set)
        ):
            required_salt_modules = required_salt_modules[0]
        required_salt_modules = set(required_salt_modules)
        not_available_modules = check_required_sminion_attributes(
            "functions", required_salt_modules
        )

        if not_available_modules:
            item._skipped_by_mark = True
            if len(not_available_modules) == 1:
                pytest.skip(
                    "Salt module '{}' is not available".format(*not_available_modules)
                )
            pytest.skip(
                "Salt modules not available: {}".format(
                    ", ".join(not_available_modules)
                )
            )

    requires_salt_states_marker = item.get_closest_marker("requires_salt_states")
    if requires_salt_states_marker is not None:
        required_salt_states = requires_salt_states_marker.args
        if len(required_salt_states) == 1 and isinstance(
            required_salt_states[0], (list, tuple, set)
        ):
            required_salt_states = required_salt_states[0]
        required_salt_states = set(required_salt_states)
        not_available_states = check_required_sminion_attributes(
            "states", required_salt_states
        )

        if not_available_states:
            item._skipped_by_mark = True
            if len(not_available_states) == 1:
                pytest.skip(
                    "Salt state module '{}' is not available".format(
                        *not_available_states
                    )
                )
            pytest.skip(
                "Salt state modules not available: {}".format(
                    ", ".join(not_available_states)
                )
            )

    if salt.utils.platform.is_windows():
        unit_tests_paths = (
            str(TESTS_DIR / "unit"),
            str(PYTESTS_DIR / "unit"),
        )
        if not str(pathlib.Path(item.fspath).resolve()).startswith(unit_tests_paths):
            # Unit tests are whitelisted on windows by default, so, we're only
            # after all other tests
            windows_whitelisted_marker = item.get_closest_marker("windows_whitelisted")
            if windows_whitelisted_marker is None:
                item._skipped_by_mark = True
                pytest.skip("Test is not whitelisted for Windows")


# <---- Test Setup ---------------------------------------------------------------------------------------------------


# ----- Test Groups Selection --------------------------------------------------------------------------------------->
def get_group_size_and_start(total_items, total_groups, group_id):
    """
    Calculate group size and start index.
    """
    base_size = total_items // total_groups
    rem = total_items % total_groups

    start = base_size * (group_id - 1) + min(group_id - 1, rem)
    size = base_size + 1 if group_id <= rem else base_size

    return (start, size)


def get_group(items, total_groups, group_id):
    """
    Get the items from the passed in group based on group size.
    """
    if not 0 < group_id <= total_groups:
        raise ValueError("Invalid test-group argument")

    start, size = get_group_size_and_start(len(items), total_groups, group_id)
    selected = items[start : start + size]
    deselected = items[:start] + items[start + size :]
    assert len(selected) + len(deselected) == len(items)
    return selected, deselected


def groups_collection_modifyitems(config, items):
    group_count = config.getoption("test-group-count")
    group_id = config.getoption("test-group")

    if not group_count or not group_id:
        # We're not selection tests using groups, don't do any filtering
        return

    total_items = len(items)

    tests_in_group, deselected = get_group(items, group_count, group_id)
    # Replace all items in the list
    items[:] = tests_in_group
    if deselected:
        config.hook.pytest_deselected(items=deselected)

    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    terminal_reporter.write(
        "Running test group #{} ({} tests)\n".format(group_id, len(items)),
        yellow=True,
    )


# <---- Test Groups Selection ----------------------------------------------------------------------------------------


# ----- Fixtures Overrides ------------------------------------------------------------------------------------------>
@pytest.fixture(scope="session")
def salt_factories_config():
    """
    Return a dictionary with the keyworkd arguments for FactoriesManager
    """
    return {
        "code_dir": str(CODE_DIR),
        "inject_coverage": MAYBE_RUN_COVERAGE,
        "inject_sitecustomize": MAYBE_RUN_COVERAGE,
        "start_timeout": 120
        if (os.environ.get("JENKINS_URL") or os.environ.get("CI"))
        else 60,
    }


# <---- Fixtures Overrides -------------------------------------------------------------------------------------------


# ----- Salt Factories ---------------------------------------------------------------------------------------------->
@pytest.fixture(scope="session")
def integration_files_dir(salt_factories):
    """
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = salt_factories.root_dir / "integration-files"
    dirname.mkdir(exist_ok=True)
    for child in (PYTESTS_DIR / "integration" / "files").iterdir():
        if child.is_dir():
            shutil.copytree(str(child), str(dirname / child.name))
        else:
            shutil.copyfile(str(child), str(dirname / child.name))
    return dirname


@pytest.fixture(scope="session")
def state_tree_root_dir(integration_files_dir):
    """
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = integration_files_dir / "state-tree"
    dirname.mkdir(exist_ok=True)
    return dirname


@pytest.fixture(scope="session")
def pillar_tree_root_dir(integration_files_dir):
    """
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = integration_files_dir / "pillar-tree"
    dirname.mkdir(exist_ok=True)
    return dirname


@pytest.fixture(scope="session")
def base_env_state_tree_root_dir(state_tree_root_dir):
    """
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = state_tree_root_dir / "base"
    dirname.mkdir(exist_ok=True)
    RUNTIME_VARS.TMP_STATE_TREE = str(dirname.resolve())
    RUNTIME_VARS.TMP_BASEENV_STATE_TREE = RUNTIME_VARS.TMP_STATE_TREE
    return dirname


@pytest.fixture(scope="session")
def prod_env_state_tree_root_dir(state_tree_root_dir):
    """
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = state_tree_root_dir / "prod"
    dirname.mkdir(exist_ok=True)
    RUNTIME_VARS.TMP_PRODENV_STATE_TREE = str(dirname.resolve())
    return dirname


@pytest.fixture(scope="session")
def base_env_pillar_tree_root_dir(pillar_tree_root_dir):
    """
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = pillar_tree_root_dir / "base"
    dirname.mkdir(exist_ok=True)
    RUNTIME_VARS.TMP_PILLAR_TREE = str(dirname.resolve())
    RUNTIME_VARS.TMP_BASEENV_PILLAR_TREE = RUNTIME_VARS.TMP_PILLAR_TREE
    return dirname


@pytest.fixture(scope="session")
def ext_pillar_file_tree_root_dir(pillar_tree_root_dir):
    """
    Fixture which returns the salt pillar file tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = pillar_tree_root_dir / "file-tree"
    dirname.mkdir(exist_ok=True)
    return dirname


@pytest.fixture(scope="session")
def prod_env_pillar_tree_root_dir(pillar_tree_root_dir):
    """
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = pillar_tree_root_dir / "prod"
    dirname.mkdir(exist_ok=True)
    RUNTIME_VARS.TMP_PRODENV_PILLAR_TREE = str(dirname.resolve())
    return dirname


@pytest.fixture(scope="session")
def salt_syndic_master_factory(
    request,
    salt_factories,
    base_env_state_tree_root_dir,
    base_env_pillar_tree_root_dir,
    prod_env_state_tree_root_dir,
    prod_env_pillar_tree_root_dir,
):
    root_dir = salt_factories.get_root_dir_for_daemon("syndic_master")
    conf_dir = root_dir / "conf"
    conf_dir.mkdir(exist_ok=True)

    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "syndic_master")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())

        tests_known_hosts_file = str(root_dir / "salt_ssh_known_hosts")
        with salt.utils.files.fopen(tests_known_hosts_file, "w") as known_hosts:
            known_hosts.write("")

    config_defaults["root_dir"] = str(root_dir)
    config_defaults["known_hosts_file"] = tests_known_hosts_file
    config_defaults["syndic_master"] = "localhost"
    config_defaults["transport"] = request.config.getoption("--transport")

    config_overrides = {"log_level_logfile": "quiet"}
    ext_pillar = []
    if salt.utils.platform.is_windows():
        ext_pillar.append(
            {"cmd_yaml": "type {}".format(os.path.join(RUNTIME_VARS.FILES, "ext.yaml"))}
        )
    else:
        ext_pillar.append(
            {"cmd_yaml": "cat {}".format(os.path.join(RUNTIME_VARS.FILES, "ext.yaml"))}
        )

    # We need to copy the extension modules into the new master root_dir or
    # it will be prefixed by it
    extension_modules_path = str(root_dir / "extension_modules")
    if not os.path.exists(extension_modules_path):
        shutil.copytree(
            os.path.join(RUNTIME_VARS.FILES, "extension_modules"),
            extension_modules_path,
        )

    # Copy the autosign_file to the new  master root_dir
    autosign_file_path = str(root_dir / "autosign_file")
    shutil.copyfile(
        os.path.join(RUNTIME_VARS.FILES, "autosign_file"), autosign_file_path
    )
    # all read, only owner write
    autosign_file_permissions = (
        stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
    )
    os.chmod(autosign_file_path, autosign_file_permissions)

    config_overrides.update(
        {
            "ext_pillar": ext_pillar,
            "extension_modules": extension_modules_path,
            "file_roots": {
                "base": [
                    str(base_env_state_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "file", "base"),
                ],
                # Alternate root to test __env__ choices
                "prod": [
                    str(prod_env_state_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "file", "prod"),
                ],
            },
            "pillar_roots": {
                "base": [
                    str(base_env_pillar_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "pillar", "base"),
                ],
                "prod": [str(prod_env_pillar_tree_root_dir)],
            },
        }
    )

    factory = salt_factories.salt_master_daemon(
        "syndic_master",
        order_masters=True,
        defaults=config_defaults,
        overrides=config_overrides,
        extra_cli_arguments_after_first_start_failure=["--log-level=debug"],
    )
    return factory


@pytest.fixture(scope="session")
def salt_syndic_factory(salt_factories, salt_syndic_master_factory):
    config_defaults = {"master": None, "minion": None, "syndic": None}
    with salt.utils.files.fopen(os.path.join(RUNTIME_VARS.CONF_DIR, "syndic")) as rfh:
        opts = yaml.deserialize(rfh.read())

        opts["hosts.file"] = os.path.join(RUNTIME_VARS.TMP, "hosts")
        opts["aliases.file"] = os.path.join(RUNTIME_VARS.TMP, "aliases")
        opts["transport"] = salt_syndic_master_factory.config["transport"]
        config_defaults["syndic"] = opts
    config_overrides = {"log_level_logfile": "quiet"}
    factory = salt_syndic_master_factory.salt_syndic_daemon(
        "syndic",
        defaults=config_defaults,
        overrides=config_overrides,
        extra_cli_arguments_after_first_start_failure=["--log-level=debug"],
    )
    return factory


@pytest.fixture(scope="session")
def salt_master_factory(
    salt_factories,
    salt_syndic_master_factory,
    base_env_state_tree_root_dir,
    base_env_pillar_tree_root_dir,
    prod_env_state_tree_root_dir,
    prod_env_pillar_tree_root_dir,
    ext_pillar_file_tree_root_dir,
):
    root_dir = salt_factories.get_root_dir_for_daemon("master")
    conf_dir = root_dir / "conf"
    conf_dir.mkdir(exist_ok=True)

    with salt.utils.files.fopen(os.path.join(RUNTIME_VARS.CONF_DIR, "master")) as rfh:
        config_defaults = yaml.deserialize(rfh.read())

        tests_known_hosts_file = str(root_dir / "salt_ssh_known_hosts")
        with salt.utils.files.fopen(tests_known_hosts_file, "w") as known_hosts:
            known_hosts.write("")

    config_defaults["root_dir"] = str(root_dir)
    config_defaults["known_hosts_file"] = tests_known_hosts_file
    config_defaults["syndic_master"] = "localhost"
    config_defaults["transport"] = salt_syndic_master_factory.config["transport"]

    config_overrides = {"log_level_logfile": "quiet"}
    ext_pillar = []
    if salt.utils.platform.is_windows():
        ext_pillar.append(
            {"cmd_yaml": "type {}".format(os.path.join(RUNTIME_VARS.FILES, "ext.yaml"))}
        )
    else:
        ext_pillar.append(
            {"cmd_yaml": "cat {}".format(os.path.join(RUNTIME_VARS.FILES, "ext.yaml"))}
        )
    ext_pillar.append(
        {
            "file_tree": {
                "root_dir": str(ext_pillar_file_tree_root_dir),
                "follow_dir_links": False,
                "keep_newline": True,
            }
        }
    )
    config_overrides["pillar_opts"] = True

    # We need to copy the extension modules into the new master root_dir or
    # it will be prefixed by it
    extension_modules_path = str(root_dir / "extension_modules")
    if not os.path.exists(extension_modules_path):
        shutil.copytree(
            os.path.join(RUNTIME_VARS.FILES, "extension_modules"),
            extension_modules_path,
        )

    # Copy the autosign_file to the new  master root_dir
    autosign_file_path = str(root_dir / "autosign_file")
    shutil.copyfile(
        os.path.join(RUNTIME_VARS.FILES, "autosign_file"), autosign_file_path
    )
    # all read, only owner write
    autosign_file_permissions = (
        stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
    )
    os.chmod(autosign_file_path, autosign_file_permissions)

    config_overrides.update(
        {
            "ext_pillar": ext_pillar,
            "extension_modules": extension_modules_path,
            "file_roots": {
                "base": [
                    str(base_env_state_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "file", "base"),
                ],
                # Alternate root to test __env__ choices
                "prod": [
                    str(prod_env_state_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "file", "prod"),
                ],
            },
            "pillar_roots": {
                "base": [
                    str(base_env_pillar_tree_root_dir),
                    os.path.join(RUNTIME_VARS.FILES, "pillar", "base"),
                ],
                "prod": [str(prod_env_pillar_tree_root_dir)],
            },
        }
    )

    # Let's copy over the test cloud config files and directories into the running master config directory
    for entry in os.listdir(RUNTIME_VARS.CONF_DIR):
        if not entry.startswith("cloud"):
            continue
        source = os.path.join(RUNTIME_VARS.CONF_DIR, entry)
        dest = str(conf_dir / entry)
        if os.path.isdir(source):
            shutil.copytree(source, dest)
        else:
            shutil.copyfile(source, dest)

    factory = salt_syndic_master_factory.salt_master_daemon(
        "master",
        defaults=config_defaults,
        overrides=config_overrides,
        extra_cli_arguments_after_first_start_failure=["--log-level=debug"],
    )
    return factory


@pytest.fixture(scope="session")
def salt_minion_factory(salt_master_factory):
    with salt.utils.files.fopen(os.path.join(RUNTIME_VARS.CONF_DIR, "minion")) as rfh:
        config_defaults = yaml.deserialize(rfh.read())
    config_defaults["hosts.file"] = os.path.join(RUNTIME_VARS.TMP, "hosts")
    config_defaults["aliases.file"] = os.path.join(RUNTIME_VARS.TMP, "aliases")
    config_defaults["transport"] = salt_master_factory.config["transport"]

    config_overrides = {
        "log_level_logfile": "quiet",
        "file_roots": salt_master_factory.config["file_roots"].copy(),
        "pillar_roots": salt_master_factory.config["pillar_roots"].copy(),
    }

    virtualenv_binary = get_virtualenv_binary_path()
    if virtualenv_binary:
        config_overrides["venv_bin"] = virtualenv_binary
    factory = salt_master_factory.salt_minion_daemon(
        "minion",
        defaults=config_defaults,
        overrides=config_overrides,
        extra_cli_arguments_after_first_start_failure=["--log-level=debug"],
    )
    factory.after_terminate(
        pytest.helpers.remove_stale_minion_key, salt_master_factory, factory.id
    )
    return factory


@pytest.fixture(scope="session")
def salt_sub_minion_factory(salt_master_factory):
    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "sub_minion")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())
    config_defaults["hosts.file"] = os.path.join(RUNTIME_VARS.TMP, "hosts")
    config_defaults["aliases.file"] = os.path.join(RUNTIME_VARS.TMP, "aliases")
    config_defaults["transport"] = salt_master_factory.config["transport"]

    config_overrides = {
        "log_level_logfile": "quiet",
        "file_roots": salt_master_factory.config["file_roots"].copy(),
        "pillar_roots": salt_master_factory.config["pillar_roots"].copy(),
    }

    virtualenv_binary = get_virtualenv_binary_path()
    if virtualenv_binary:
        config_overrides["venv_bin"] = virtualenv_binary
    factory = salt_master_factory.salt_minion_daemon(
        "sub_minion",
        defaults=config_defaults,
        overrides=config_overrides,
        extra_cli_arguments_after_first_start_failure=["--log-level=debug"],
    )
    factory.after_terminate(
        pytest.helpers.remove_stale_minion_key, salt_master_factory, factory.id
    )
    return factory


@pytest.fixture(scope="session")
def salt_cli(salt_master_factory):
    return salt_master_factory.salt_cli()


@pytest.fixture(scope="session")
def salt_cp_cli(salt_master_factory):
    return salt_master_factory.salt_cp_cli()


@pytest.fixture(scope="session")
def salt_key_cli(salt_master_factory):
    return salt_master_factory.salt_key_cli()


@pytest.fixture(scope="session")
def salt_run_cli(salt_master_factory):
    return salt_master_factory.salt_run_cli()


@pytest.fixture(scope="session")
def salt_call_cli(salt_minion_factory):
    return salt_minion_factory.salt_call_cli()


@pytest.fixture(scope="session", autouse=True)
def bridge_pytest_and_runtests(
    reap_stray_processes,
    salt_factories,
    salt_syndic_master_factory,
    salt_syndic_factory,
    salt_master_factory,
    salt_minion_factory,
    salt_sub_minion_factory,
    sshd_config_dir,
):
    # Make sure unittest2 uses the pytest generated configuration
    RUNTIME_VARS.RUNTIME_CONFIGS["master"] = freeze(salt_master_factory.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["minion"] = freeze(salt_minion_factory.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["sub_minion"] = freeze(salt_sub_minion_factory.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["syndic_master"] = freeze(
        salt_syndic_master_factory.config
    )
    RUNTIME_VARS.RUNTIME_CONFIGS["syndic"] = freeze(salt_syndic_factory.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["client_config"] = freeze(
        salt.config.client_config(salt_master_factory.config["conf_file"])
    )

    # Make sure unittest2 classes know their paths
    RUNTIME_VARS.TMP_ROOT_DIR = str(salt_factories.root_dir.resolve())
    RUNTIME_VARS.TMP_CONF_DIR = os.path.dirname(salt_master_factory.config["conf_file"])
    RUNTIME_VARS.TMP_MINION_CONF_DIR = os.path.dirname(
        salt_minion_factory.config["conf_file"]
    )
    RUNTIME_VARS.TMP_SUB_MINION_CONF_DIR = os.path.dirname(
        salt_sub_minion_factory.config["conf_file"]
    )
    RUNTIME_VARS.TMP_SYNDIC_MASTER_CONF_DIR = os.path.dirname(
        salt_syndic_master_factory.config["conf_file"]
    )
    RUNTIME_VARS.TMP_SYNDIC_MINION_CONF_DIR = os.path.dirname(
        salt_syndic_factory.config["conf_file"]
    )
    RUNTIME_VARS.TMP_SSH_CONF_DIR = str(sshd_config_dir)


@pytest.fixture(scope="session")
def sshd_config_dir(salt_factories):
    config_dir = salt_factories.get_root_dir_for_daemon("sshd")
    yield config_dir
    shutil.rmtree(str(config_dir), ignore_errors=True)


@pytest.fixture(scope="module")
def sshd_server(salt_factories, sshd_config_dir, salt_master):
    sshd_config_dict = {
        "Protocol": "2",
        # Turn strict modes off so that we can operate in /tmp
        "StrictModes": "no",
        # Logging
        "SyslogFacility": "AUTH",
        "LogLevel": "INFO",
        # Authentication:
        "LoginGraceTime": "120",
        "PermitRootLogin": "without-password",
        "PubkeyAuthentication": "yes",
        # Don't read the user's ~/.rhosts and ~/.shosts files
        "IgnoreRhosts": "yes",
        "HostbasedAuthentication": "no",
        # To enable empty passwords, change to yes (NOT RECOMMENDED)
        "PermitEmptyPasswords": "no",
        # Change to yes to enable challenge-response passwords (beware issues with
        # some PAM modules and threads)
        "ChallengeResponseAuthentication": "no",
        # Change to no to disable tunnelled clear text passwords
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
        "X11DisplayOffset": "10",
        "PrintMotd": "no",
        "PrintLastLog": "yes",
        "TCPKeepAlive": "yes",
        "AcceptEnv": "LANG LC_*",
        "Subsystem": "sftp /usr/lib/openssh/sftp-server",
        "UsePAM": "yes",
    }
    factory = salt_factories.get_sshd_daemon(
        sshd_config_dict=sshd_config_dict,
        config_dir=sshd_config_dir,
    )
    with factory.started():
        yield factory


@pytest.fixture(scope="module")
def salt_ssh_roster_file(sshd_server, salt_master):
    roster_contents = """
    localhost:
      host: 127.0.0.1
      port: {}
      user: {}
      mine_functions:
        test.arg: ['itworked']
    """.format(
        sshd_server.listen_port, RUNTIME_VARS.RUNNING_TESTS_USER
    )
    if salt.utils.platform.is_darwin():
        roster_contents += "  set_path: $PATH:/usr/local/bin/\n"
    with pytest.helpers.temp_file(
        "roster", roster_contents, salt_master.config_dir
    ) as roster_file:
        yield roster_file


# <---- Salt Factories -----------------------------------------------------------------------------------------------


# ----- From Filenames Test Selection ------------------------------------------------------------------------------->
def _match_to_test_file(match):
    parts = match.split(".")
    test_module_path = TESTS_DIR.joinpath(*parts)
    if test_module_path.exists():
        return test_module_path
    parts[-1] += ".py"
    return TESTS_DIR.joinpath(*parts).relative_to(CODE_DIR)


def from_filenames_collection_modifyitems(config, items):
    from_filenames = config.getoption("--from-filenames")
    if not from_filenames:
        # Don't do anything
        return

    terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
    terminal_reporter.ensure_newline()
    terminal_reporter.section(
        "From Filenames(--from-filenames) Test Selection", sep=">"
    )
    errors = []
    test_module_selections = []
    changed_files_selections = []
    from_filenames_paths = set()
    for path in [path.strip() for path in from_filenames.split(",")]:
        # Make sure that, no matter what kind of path we're passed, Windows or Posix path,
        # we resolve it to the platform slash separator
        properly_slashed_path = pathlib.Path(
            path.replace("\\", os.sep).replace("/", os.sep)
        )
        if not properly_slashed_path.exists():
            errors.append("{}: Does not exist".format(properly_slashed_path))
            continue
        if properly_slashed_path.is_absolute():
            # In this case, this path is considered to be a file containing a line separated list
            # of files to consider
            contents = properly_slashed_path.read_text()
            for sep in ("\r\n", "\\r\\n", "\\n"):
                contents = contents.replace(sep, "\n")
            for line in contents.split("\n"):
                line_path = pathlib.Path(
                    line.strip().replace("\\", os.sep).replace("/", os.sep)
                )
                if not line_path.exists():
                    errors.append(
                        "{}: Does not exist. Source {}".format(
                            line_path, properly_slashed_path
                        )
                    )
                    continue
                changed_files_selections.append(
                    "{}: Source {}".format(line_path, properly_slashed_path)
                )
                from_filenames_paths.add(line_path)
            continue
        changed_files_selections.append(
            "{}: Source --from-filenames".format(properly_slashed_path)
        )
        from_filenames_paths.add(properly_slashed_path)

    # Let's start collecting test modules
    test_module_paths = set()

    filename_map = yaml.deserialize((TESTS_DIR / "filename_map.yml").read_text())
    # Let's add the match all rule
    for rule, matches in filename_map.items():
        if rule == "*":
            for match in matches:
                test_module_paths.add(_match_to_test_file(match))
            break

    # Let's now go through the list of files gathered
    for path in from_filenames_paths:
        if path.as_posix().startswith("tests/"):
            if path.name == "conftest.py":
                # This is not a test module, but consider any test_*.py files in child directories
                for match in path.parent.rglob("test_*.py"):
                    test_module_selections.append(
                        "{}: Source '{}/test_*.py' recursive glob match because '{}' was modified".format(
                            match, path.parent, path
                        )
                    )
                    test_module_paths.add(match)
                continue
            # Tests in the listing don't require additional matching and will be added to the
            # list of tests to run
            test_module_selections.append("{}: Source --from-filenames".format(path))
            test_module_paths.add(path)
            continue
        if path.name == "setup.py" or path.as_posix().startswith("salt/"):
            if path.name == "__init__.py":
                # No direct matching
                continue

            # Let's try a direct match between the passed file and possible test modules
            glob_patterns = (
                # salt/version.py ->
                #    tests/unit/test_version.py
                #    tests/pytests/unit/test_version.py
                "**/test_{}".format(path.name),
                # salt/modules/grains.py ->
                #    tests/pytests/integration/modules/grains/tests_*.py
                # salt/modules/saltutil.py ->
                #    tests/pytests/integration/modules/saltutil/test_*.py
                "**/{}/test_*.py".format(path.stem),
                # salt/modules/config.py ->
                #    tests/unit/modules/test_config.py
                #    tests/integration/modules/test_config.py
                #    tests/pytests/unit/modules/test_config.py
                #    tests/pytests/integration/modules/test_config.py
                "**/{}/test_{}".format(path.parent.name, path.name),
            )
            for pattern in glob_patterns:
                for match in TESTS_DIR.rglob(pattern):
                    relative_path = match.relative_to(CODE_DIR)
                    test_module_selections.append(
                        "{}: Source '{}' glob pattern match".format(
                            relative_path, pattern
                        )
                    )
                    test_module_paths.add(relative_path)

            # Do we have an entry in tests/filename_map.yml
            for rule, matches in filename_map.items():
                if rule == "*":
                    continue
                elif "|" in rule:
                    # This is regex
                    if re.match(rule, path.as_posix()):
                        for match in matches:
                            test_module_paths.add(_match_to_test_file(match))
                            test_module_selections.append(
                                "{}: Source '{}' regex match from 'tests/filename_map.yml'".format(
                                    match, rule
                                )
                            )
                elif "*" in rule or "\\" in rule:
                    # Glob matching
                    for filerule in CODE_DIR.glob(rule):
                        if not filerule.exists():
                            continue
                        filerule = filerule.relative_to(CODE_DIR)
                        if filerule != path:
                            continue
                        for match in matches:
                            match_path = _match_to_test_file(match)
                            test_module_selections.append(
                                "{}: Source '{}' file rule from 'tests/filename_map.yml'".format(
                                    match_path, filerule
                                )
                            )
                            test_module_paths.add(match_path)
                else:
                    if path.as_posix() != rule:
                        continue
                    # Direct file paths as rules
                    filerule = pathlib.Path(rule)
                    if not filerule.exists():
                        continue
                    for match in matches:
                        match_path = _match_to_test_file(match)
                        test_module_selections.append(
                            "{}: Source '{}' direct file rule from 'tests/filename_map.yml'".format(
                                match_path, filerule
                            )
                        )
                        test_module_paths.add(match_path)
            continue
        else:
            errors.append("{}: Don't know what to do with this path".format(path))

    if errors:
        terminal_reporter.write("Errors:\n", bold=True)
        for error in errors:
            terminal_reporter.write(" * {}\n".format(error))
    if changed_files_selections:
        terminal_reporter.write("Changed files collected:\n", bold=True)
        for selection in changed_files_selections:
            terminal_reporter.write(" * {}\n".format(selection))
    if test_module_selections:
        terminal_reporter.write("Selected test modules:\n", bold=True)
        for selection in test_module_selections:
            terminal_reporter.write(" * {}\n".format(selection))
    terminal_reporter.section(
        "From Filenames(--from-filenames) Test Selection", sep="<"
    )
    terminal_reporter.ensure_newline()

    selected = []
    deselected = []
    for item in items:
        itempath = pathlib.Path(str(item.fspath)).resolve().relative_to(CODE_DIR)
        if itempath in test_module_paths:
            selected.append(item)
        else:
            deselected.append(item)

    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


# <---- From Filenames Test Selection --------------------------------------------------------------------------------


# ----- Custom Fixtures --------------------------------------------------------------------------------------------->
@pytest.fixture(scope="session")
def reap_stray_processes():
    # Run tests
    yield

    children = psutil.Process(os.getpid()).children(recursive=True)
    if not children:
        log.info("No astray processes found")
        return

    def on_terminate(proc):
        log.debug("Process %s terminated with exit code %s", proc, proc.returncode)

    if children:
        # Reverse the order, sublings first, parents after
        children.reverse()
        log.warning(
            "Test suite left %d astray processes running. Killing those processes:\n%s",
            len(children),
            pprint.pformat(children),
        )

        _, alive = psutil.wait_procs(children, timeout=3, callback=on_terminate)
        for child in alive:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                continue

        _, alive = psutil.wait_procs(alive, timeout=3, callback=on_terminate)
        if alive:
            # Give up
            for child in alive:
                log.warning(
                    "Process %s survived SIGKILL, giving up:\n%s",
                    child,
                    pprint.pformat(child.as_dict()),
                )


@pytest.fixture(scope="session")
def sminion():
    return create_sminion()


@pytest.fixture(scope="session")
def grains(sminion):
    return sminion.opts["grains"].copy()


@pytest.fixture
def ssl_webserver(integration_files_dir, scope="module"):
    """
    spins up an https webserver.
    """
    if sys.version_info < (3, 5, 3):
        pytest.skip("Python versions older than 3.5.3 do not define `ssl.PROTOCOL_TLS`")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain(
        str(integration_files_dir / "https" / "cert.pem"),
        str(integration_files_dir / "https" / "key.pem"),
    )

    webserver = Webserver(root=str(integration_files_dir), ssl_opts=context)
    webserver.start()
    yield webserver
    webserver.stop()


# <---- Custom Fixtures ----------------------------------------------------------------------------------------------




KNOWN_ISSUES_INTEGRATION = {
    'ignore_list': {
        'common': [
            'tests/integration/externalapi/test_venafiapi.py',
            'test_state.py::OrchEventTest::test_parallel_orchestrations',
            'test_state.py::StateModuleTest::test_requisites_onfail_any',
            'files/file/base/*',           # should no be included
            'utils/test_reactor.py',       # not yet implemented
            '*::SaltnadoTestCase::*',                  # these are not actual tests
            'cloud/providers/msazure.py',
            'modules/git.py',
            'cloud/helpers/virtualbox.py',

            'utils/*',

            # Running following tests causes unsuccessfully close
            # of forked processes. This will cause "hanging" jenkins jobs.
            'states/supervisord.py',
            '*::MasterTest::test_exit_status_correct_usage',
            '*::ProxyTest::test_exit_status_correct_usage',
            '*::FileTest::test_issue_2227_file_append',
            '*::FileTest::test_issue_8947_utf8_sls',

            # Evil test
            'reactor/reactor.py', # This test causes "py.test" never finishes
            # 'runners/fileserver.py::FileserverTest::test_clear_file_list_cache',  # this test hangs
            'runners/fileserver.py',  # workaround for comment above
            # 'wheel/key.py::KeyWheelModuleTest::test_list_all',  # ERROR at teardown
            '*/wheel/key.py',  # workaround for comment above
            '*/wheel/client.py',
            '*/virtualenv.py',
            '*/states/user.py',
            '*states/svn.py',
            '*/kitchen/tests/wordpress/*',
            'pillar/test_git_pillar.py',

            # We are not interested in the NetapiClientTests
            '*/netapi/test_client.py',

            # This makes a request to github.com
            '*/modules/ssh.py',

            # CRON is not installed on toaster images and cron tests are not designed for SUSE.
            '*/states/test_cron.py',

            # NEED INVESTIGATION
            '*rest_tornado/test_app.py::TestSaltAPIHandler::test_multi_local_async_post',
            '*rest_tornado/test_app.py::TestSaltAPIHandler::test_multi_local_async_post_multitoken',
            '*rest_tornado/test_app.py::TestSaltAPIHandler::test_simple_local_async_post',
            '*rest_tornado/test_app.py::TestSaltAPIHandler::test_simple_local_runner_post',
            '*/test_state.py::StateModuleTest::test_onchanges_in_requisite',
            '*/test_state.py::StateModuleTest::test_onchanges_requisite',
            '*/test_state.py::StateModuleTest::test_onchanges_requisite_multiple',
            '*/test_state.py::StateModuleTest::test_requisites_onchanges_any',
            '*/runners/test_state.py::StateRunnerTest::test_orchestrate_retcode',
            '*/shell/test_call.py::CallTest::test_issue_14979_output_file_permissions',
            '*/shell/test_call.py::CallTest::test_issue_15074_output_file_append',
            '*/shell/test_call.py::CallTest::test_issue_2731_masterless',
            '*/modules/ssh.py',
            '*/proxy/test_shell.py',  # proxy minion is not starting

            # After switch to M2Crypto
            'cloud/clouds/test_digitalocean.py', # ModuleNotFoundError: No module named 'Crypto'
        ],
        'rhel6': [
            # Avoid error due:
            # [Errno 1] _ssl.c:492: error:1409442E:SSL routines:SSL3_READ_BYTES:tlsv1 alert protocol version
            '*/modules/gem.py',
        ],
        # disable 2017.7.1 on python 2.6
        'rhel6/products-next': ['*'],
        'sles11sp3/products-next': ['*'],
        'sles11sp4/products-next': ['*'],
        'sles11sp3': ['*/modules/gem.py', '*/modules/ssh.py'],
        'sles11sp4': ['*/modules/gem.py', '*/modules/ssh.py'],
    },
    'xfail_list': {
        'common': [
            # Always failing
            '*sysmod.py::SysModuleTest::test_valid_docs',
            'cloud/providers/virtualbox.py::BaseVirtualboxTests::test_get_manager',

            'modules/timezone.py::TimezoneLinuxModuleTest::test_get_hwclock',
            'states/git.py::GitTest::test_latest_changed_local_branch_rev_develop',
            'states/git.py::GitTest::test_latest_changed_local_branch_rev_head',
            'states/git.py::GitTest::test_latest_fast_forward',
            'states/git.py::LocalRepoGitTest::test_renamed_default_branch',

            'loader/ext_grains.py::LoaderGrainsTest::test_grains_overwrite',
            'loader/ext_modules.py::LoaderOverridesTest::test_overridden_internal',

            'modules/decorators.py::DecoratorTest::test_depends',
            'modules/decorators.py::DecoratorTest::test_depends_will_not_fallback',
            'modules/decorators.py::DecoratorTest::test_missing_depends_will_fallback',

            # Sometimes failing in jenkins.
            'shell/call.py::CallTest::test_issue_14979_output_file_permissions',
            'shell/call.py::CallTest::test_issue_15074_output_file_append',
            'shell/call.py::CallTest::test_issue_2731_masterless',
            'shell/matcher.py::MatchTest::test_grain',

            'netapi/rest_tornado/test_app.py::TestSaltAPIHandler::test_simple_local_post_only_dictionary_request',
            'shell/master_tops.py::MasterTopsTest::test_custom_tops_gets_utilized',
            'states/svn.py::SvnTest::test_latest', # sles12sp1
            'states/svn.py::SvnTest::test_latest_empty_dir', # sles12sp1
            'runners/state.py::StateRunnerTest::test_orchestrate_output', # sles12sp1 rhel7
            'modules/test_saltutil.py::SaltUtilSyncPillarTest::test_pillar_refresh', # sles12sp2
            '*::test_issue_7754',

            '*test_fileserver.py::FileserverTest::test_symlink_list',
            '*test_fileserver.py::FileserverTest::test_empty_dir_list',
            '*test_timezone.py::TimezoneLinuxModuleTest::test_get_hwclock',
            '*test_file.py::FileTest::test_managed_check_cmd',
            'modules/test_network.py::NetworkTest::test_network_ping', # Bad test implementation

            # Needs investigation. Setting them to xfail to have a "new green start" on March 15th
            # see https://github.com/SUSE/spacewalk/issues/14284
            'states/test_match.py::StateMatchTest::test_issue_2167_ipcidr_no_AttributeError',
            'states/test_file.py::FileTest::test_directory_broken_symlink',
            'shell/test_matcher.py::MatchTest::test_ipcidr',
            'netapi/rest_cherrypy/test_app.py::TestJobs::test_all_jobs',
            'netapi/rest_cherrypy/test_app.py::TestAuth::test_webhook_auth',
            'modules/test_saltutil.py::SaltUtilModuleTest::test_wheel_just_function',
            'modules/test_network.py::NetworkTest::test_network_netstat',
            'modules/test_cp.py::CPModuleTest::test_get_dir_templated_paths',
            'modules/test_cmdmod.py::CMDModuleTest::test_script_retcode',
            'modules/test_cmdmod.py::CMDModuleTest::test_script_cwd_with_space',
            'modules/test_cmdmod.py::CMDModuleTest::test_script_cwd',
            'modules/test_cmdmod.py::CMDModuleTest::test_script',
            'modules/test_cmdmod.py::CMDModuleTest::test_has_exec',
            'modules/test_cmdmod.py::CMDModuleTest::test_exec_code_with_single_arg',
            'modules/test_cmdmod.py::CMDModuleTest::test_exec_code_with_multiple_args',
            'modules/test_cmdmod.py::CMDModuleTest::test_exec_code',

            # Failing in 3003.3
            'modules/saltutil/test_wheel.py::test_wheel_just_function',
            'modules/test_pip.py::PipModuleTest::test_pip_install_multiple_editables',
            'states/test_pip_state.py::PipStateTest::test_issue_2028_pip_installed_state',
            'cli/test_matcher.py::test_ipcidr',
        ],
        'rhel6': [
            'cloud/providers/virtualbox.py::CreationDestructionVirtualboxTests::test_vm_creation_and_destruction',
            'cloud/providers/virtualbox.py::CloneVirtualboxTests::test_create_machine',
            'cloud/providers/virtualbox.py::BootVirtualboxTests::test_start_stop',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attribute_with_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_imachine_object_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_override_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_unknown_object',
            'fileserver/roots_test.py::RootsTest::test_symlink_list',
        ],
        'rhel7': [
            'states/archive.py::ArchiveTest::test_archive_extracted_skip_verify',
            'states/archive.py::ArchiveTest::test_archive_extracted_with_root_user_and_group',
            'states/archive.py::ArchiveTest::test_archive_extracted_with_source_hash',
        ],
        'sles11sp3': [
            'cloud/providers/virtualbox.py::CreationDestructionVirtualboxTests::test_vm_creation_and_destruction',
            'cloud/providers/virtualbox.py::CloneVirtualboxTests::test_create_machine',
            'cloud/providers/virtualbox.py::BootVirtualboxTests::test_start_stop',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attribute_with_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_imachine_object_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_override_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_unknown_object',
            'fileserver/roots_test.py::RootsTest::test_symlink_list',
        ],
        'sles11sp4': [
            'cloud/providers/virtualbox.py::CreationDestructionVirtualboxTests::test_vm_creation_and_destruction',
            'cloud/providers/virtualbox.py::CloneVirtualboxTests::test_create_machine',
            'cloud/providers/virtualbox.py::BootVirtualboxTests::test_start_stop',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attribute_with_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_extra_nonexistent_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_imachine_object_default',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_override_attributes',
            'cloud/providers/virtualbox.py::XpcomConversionTests::test_unknown_object',
            'shell/master.py::MasterTest::test_exit_status_correct_usage',
            'states/git.py::GitTest::test_config_set_value_with_space_character',
            'states/git.py::GitTest::test_latest',
            'states/git.py::GitTest::test_latest_changed_local_branch_rev_develop',
            'states/git.py::GitTest::test_latest_changed_local_branch_rev_head',
            'states/git.py::GitTest::test_latest_empty_dir',
            'states/git.py::GitTest::test_latest_unless_no_cwd_issue_6800',
            'states/git.py::GitTest::test_latest_with_local_changes',
            'states/git.py::GitTest::test_latest_with_rev_and_submodules',
            'states/git.py::GitTest::test_numeric_rev',
            'fileserver/roots_test.py::RootsTest::test_symlink_list',
        ],
        'sles12': [
        ],
        'sles12sp1': [
        ],
        'sles12sp2': [
        ],
        'sles12sp3': [
            'modules/test_pkg.py::PkgModuleTest::test_mod_del_repo_multiline_values', # this test should not be executed on SUSE systems
        ],
        'sles15': [
            'modules/test_pkg.py::PkgModuleTest::test_mod_del_repo_multiline_values', # this test should not be executed on SUSE systems
        ],
        'ubuntu1604': [
            'shell/test_enabled.py::EnabledTest::test_shell_default_enabled', # https://github.com/saltstack/salt/issues/52898
            'shell/test_enabled.py::EnabledTest::test_template_shell', # https://github.com/saltstack/salt/issues/52898
        ],
        'ubuntu1804': [
            'shell/test_enabled.py::EnabledTest::test_shell_default_enabled', # https://github.com/saltstack/salt/issues/52898
            'shell/test_enabled.py::EnabledTest::test_template_shell', # https://github.com/saltstack/salt/issues/52898
        ],
    }
}


KNOWN_ISSUES_UNIT = {
    'ignore_list': {
        'common': [
            'test_engines.py', # Make pytest to stuck for long time after tests are executed
            'modules/test_boto3_elasticsearch.py',
            'zypp_plugins_test.py', # BogusIO missing in zypp_plugin
            'netapi/rest_tornado/test_handlers.py',
            'netapi/test_rest_tornado.py',
            'returners/smtp_return_test.py',
            'transport/zeromq_test.py',  # Prevent pytests hang after tests
            'conf_test.py::ConfTest::test_conf_master_sample_is_commented', # we have uncommented custom config
            'conf_test.py::ConfTest::test_conf_minion_sample_is_commented', # we have uncommented custom config
            'conf_test.py::ConfTest::test_conf_proxy_sample_is_commented', # we have uncommented custom config
            '*rsync_test.py::*',
            'test_module_names.py',
            'modules/darwin_sysctl_test.py',
            'states/boto_cloudwatch_event_test.py',
            'modules/boto_vpc_test.py',
            'states/boto_vpc_test.py',
            'utils/boto_test.py',
            'modules/win_ip_test.py::WinShadowTestCase::test_set_static_ip', # takes too long to execute
            'states/blockdev_test.py::BlockdevTestCase::test_formatted', # takes too long to execute
            'cloud/clouds/dimensiondata_test.py',
            'cloud/clouds/gce_test.py',
            '*/utils/test_parsers.py',
            '*/kitchen/tests/wordpress/*',
            'fileserver/test_gitfs.py',
            # NEEDS INVESTIGATION
            'test_pip.py::PipStateTest::test_install_requirements_parsing',
            '*/modules/test_useradd.py',
            'utils/cache_mods/cache_mod.py',
            'modules/test_boto_vpc.py',
            'states/test_boto_vpc.py',
            'states/test_augeas.py::AugeasTestCase::test_change_no_context_with_full_path_fail',

            # Not running tests for cheetah, mako and genshi templating
            'utils/test_templates.py::RenderTestCase::test_render_cheetah_evaluate',
            'utils/test_templates.py::RenderTestCase::test_render_cheetah_evaluate_text',
            'utils/test_templates.py::RenderTestCase::test_render_cheetah_evaluate_xml',
            'utils/test_templates.py::RenderTestCase::test_render_cheetah_sanity',
            'utils/test_templates.py::RenderTestCase::test_render_cheetah_variable',
            'utils/test_templates.py::RenderTestCase::test_render_genshi_evaluate',
            'utils/test_templates.py::RenderTestCase::test_render_genshi_evaluate_condition',
            'utils/test_templates.py::RenderTestCase::test_render_genshi_sanity',
            'utils/test_templates.py::RenderTestCase::test_render_genshi_variable',
            'utils/test_templates.py::RenderTestCase::test_render_genshi_variable_replace',
            'utils/test_templates.py::RenderTestCase::test_render_mako_evaluate',
            'utils/test_templates.py::RenderTestCase::test_render_mako_evaluate_multi',
            'utils/test_templates.py::RenderTestCase::test_render_mako_sanity',
            'utils/test_templates.py::RenderTestCase::test_render_mako_variable',

            # This produces a bad file descriptor error at the end of the testsuite, even if the tests passes
            'utils/test_thin.py::SSHThinTestCase::test_gen_thin_compression_fallback_py3',

            # contain NO_MOCK which does not exist anymore (throws ImportError)
            'cli/test_support.py',
            'modules/test_saltsupport.py',
            'utils/test_pkg.py',

            # duplicated test file, should be removed in favor of the one in tests/pytests/
            'tests/unit/modules/test_ansiblegate.py',
            # has a broken test, adding it to xfail does not work because it conflicts with tests/unit/utils/test_thin.py
            'pytests/unit/utils/test_thin.py',
            'transport/test_zeromq.py', # Leaks memory on SLE15SP2
            'transport/test_tcp.py',

            # Errors in 3003.3
            'cloud/test_map.py',

            # Problem running in Docker in SUSE Jenkins
            'tests/pytests/unit/grains/test_core.py::test_xen_virtual'

        ],
        'sles11sp4': [
            # SSLError: [Errno 1] _ssl.c:492: error:1409442E:SSL routines:SSL3_READ_BYTES:tlsv1 alert protocol version
            'modules/random_org_test.py',
            'states/test_saltutil.py',
        ],
        'rhel6': [
            # SSLError: [Errno 1] _ssl.c:492: error:1409442E:SSL routines:SSL3_READ_BYTES:tlsv1 alert protocol version
            'modules/random_org_test.py',
            'states/test_saltutil.py',
        ],
        'sles15': [
            'utils/cache_mods/cache_mod.py',
            'test_zypp_plugins.py',
            'modules/test_yumpkg.py',
        ],
    },

    'xfail_list': {
        'common': [
            # fixed in saltstack/develop
            # https://github.com/saltstack/salt/commit/7427e192baeccfee69b4887fe0c630a1afb38730#diff-3b5d15bc59b82fc8d4b15f819babf4faR70
            'test_core.py::CoreGrainsTestCase::test_parse_etc_os_release',
            'test_core.py::CoreGrainsTestCase::test_fqdns_socket_error',

            'templates/jinja_test.py::TestCustomExtensions::test_serialize_yaml_unicode',
            # not working in docker containers
            'modules/cmdmod_test.py::CMDMODTestCase::test_run',
            'conf_test.py::ConfTest::test_conf_cloud_maps_d_files_are_commented',
            'conf_test.py::ConfTest::test_conf_cloud_profiles_d_files_are_commented',
            'conf_test.py::ConfTest::test_conf_cloud_providers_d_files_are_commented',
            'utils/extend_test.py::ExtendTestCase::test_run',
            'beacons/glxinfo.py::GLXInfoBeaconTestCase::test_no_user',
            'beacons/glxinfo.py::GLXInfoBeaconTestCase::test_non_dict_config',

            # Boto failing tests
            'modules/boto_apigateway_test.py::BotoApiGatewayTestCaseBase::runTest',
            'modules/boto_cloudwatch_event_test.py::BotoCloudWatchEventTestCaseBase::runTest',
            'modules/boto_cognitoidentity_test.py::BotoCognitoIdentityTestCaseBase::runTest',
            'modules/boto_elasticsearch_domain_test.py::BotoElasticsearchDomainTestCaseBase::runTest',
            'states/boto_apigateway_test.py::BotoApiGatewayStateTestCaseBase::runTest',
            'states/boto_cognitoidentity_test.py::BotoCognitoIdentityStateTestCaseBase::runTest',
            'states/boto_elasticsearch_domain_test.py::BotoElasticsearchDomainStateTestCaseBase::runTest',

            'modules/inspect_collector_test.py::InspectorCollectorTestCase::test_file_tree',
            '*CoreGrainsTestCase::test_linux_memdata',
            'ConfTest::test_conf_master_sample_is_commented',  # this is not passing because we have custom config by default (user "salt")
            'test_cmdmod.py::CMDMODTestCase::test_run',

            'modules/test_cmdmod.py::CMDMODTestCase::test_run',  # test too slow
            '*test_yumpkg.py::YumTestCase::test_list_pkgs_with_attr',
            '*test_local_cache.py::Local_CacheTest::test_clean_old_jobs',
            '*test_local_cache.py::Local_CacheTest::test_not_clean_new_jobs',
            '*test_conf.py::ConfTest::test_conf_master_sample_is_commented',

            # After switch to M2Crypto
            'modules/test_x509.py::X509TestCase::test_create_crl', # No OpenSSL available
            'modules/test_x509.py::X509TestCase::test_revoke_certificate_with_crl', # No OpenSSL available

            # Fails due to the async batch changes
            'transport/test_ipc.py::IPCMessagePubSubCase::test_multi_client_reading',

            # Needs investigation. Setting them to xfail to have a "new green start" on March 12th
            # https://github.com/SUSE/spacewalk/issues/14263
            'states/test_network.py::NetworkTestCase::test_managed',
            'modules/test_zypperpkg.py::ZypperTestCase::test_add_repo_key_path',
            'modules/test_state.py::StateTestCase::test_show_sls',
            'modules/test_dpkg_lowpkg.py::DpkgTestCase::test_info',
            'grains/test_core.py::CoreGrainsTestCase::test_fqdn_return',
            'grains/test_core.py::CoreGrainsTestCase::test_fqdn4_empty',
            'beacons/test_cert_info.py::CertInfoBeaconTestCase::test_cert_information',
            # These also need investigation, setting to xfail for a green start for 3002.2
            'test_ext.py::VendorTornadoTest::test_vendored_tornado_import',
            'grains/test_core.py::CoreGrainsTestCase::test_core_virtual_invalid',
            'grains/test_core.py::CoreGrainsTestCase::test_core_virtual_unicode',
            'grains/test_core.py::test_get_server_id',
            'modules/test_aptpkg.py::AptPkgTestCase::test_add_repo_key_failed',
            'modules/test_aptpkg.py::AptPkgTestCase::test_list_repos',
            'utils/test_vmware.py::PrivateGetServiceInstanceTestCase::test_third_attempt_successful_connection',
            'pytests/unit/modules/test_ansiblegate.py::test_ansible_module_call',

            # Failing on 3003.3
            'beacons/test_telegram_bot_msg.py::TelegramBotMsgBeaconTestCase::test_call_no_updates',
            'beacons/test_telegram_bot_msg.py::TelegramBotMsgBeaconTestCase::test_call_telegram_return_no_updates_for_user',
            'beacons/test_telegram_bot_msg.py::TelegramBotMsgBeaconTestCase::test_call_telegram_returning_updates',
            'modules/test_zcbuildout.py::BuildoutTestCase::test_get_bootstrap_url',
            'modules/test_zcbuildout.py::BuildoutTestCase::test_get_buildout_ver',
            'modules/test_zfs.py::ZfsTestCase::test_bookmark_success',
            'modules/test_aptpkg.py::AptPkgTestCase::test_expand_repo_def',
            'modules/test_cmdmod.py::test_run_cwd_in_combination_with_runas', # Fails on docker container
            'states/test_pkgrepo.py::test_migrated_wrong_method',

            # Failing on 3004 (FileNotFoundError)
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_empty_spec',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_kwargs_match',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_kwargs_mismatch',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_mixed_match',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_mixed_mismatch',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_more_args',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_simple_forbidden',
            'tests/unit/test_auth.py::MasterACLTestCase::test_args_simple_match',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_function_glob',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_minion_glob',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_not_user_glob_all',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_publish_group',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_publish_name',
            'tests/unit/test_auth.py::MasterACLTestCase::test_master_publish_some_minions',
            'tests/unit/test_auth.py::AuthACLTestCase::test_acl_simple_allow',
            'tests/unit/test_auth.py::AuthACLTestCase::test_acl_simple_deny',
            'tests/unit/test_config.py::ConfigTestCase::test_backend_rename',
            'tests/unit/test_config.py::ConfigTestCase::test_common_prefix_stripping',
            'tests/unit/test_config.py::ConfigTestCase::test_conf_file_strings_are_unicode_for_master',
            'tests/unit/test_config.py::ConfigTestCase::test_conf_file_strings_are_unicode_for_minion',
            'tests/unit/test_config.py::ConfigTestCase::test_default_root_dir_included_in_config_root_dir',
            'tests/unit/test_config.py::ConfigTestCase::test_deploy_search_path_as_string',
            'tests/unit/test_config.py::ConfigTestCase::test_issue_5970_minion_confd_inclusion',
            'tests/unit/test_config.py::ConfigTestCase::test_load_client_config_from_environ_var',
            'tests/unit/test_config.py::ConfigTestCase::test_load_cloud_config_from_environ_var',
            'tests/unit/test_config.py::ConfigTestCase::test_load_master_config_from_environ_var',
            'tests/unit/test_config.py::ConfigTestCase::test_load_minion_config_from_environ_var',
            'tests/unit/test_config.py::ConfigTestCase::test_master_confd_inclusion',
            'tests/unit/test_config.py::ConfigTestCase::test_master_file_roots_glob',
            'tests/unit/test_config.py::ConfigTestCase::test_master_pillar_roots_glob',
            'tests/unit/test_config.py::ConfigTestCase::test_minion_config_role_master',
            'tests/unit/test_config.py::ConfigTestCase::test_minion_file_roots_glob',
            'tests/unit/test_config.py::ConfigTestCase::test_minion_pillar_roots_glob',
            'tests/unit/test_config.py::ConfigTestCase::test_mminion_config_cache_path',
            'tests/unit/test_config.py::ConfigTestCase::test_mminion_config_cache_path_overrides',
            'tests/unit/test_config.py::ConfigTestCase::test_proper_path_joining',
            'tests/unit/test_config.py::ConfigTestCase::test_sha256_is_default_for_master',
            'tests/unit/test_config.py::ConfigTestCase::test_sha256_is_default_for_minion',
            'tests/unit/test_fileclient.py::FileClientTest::test_get_file_client',
        ],
        'sles12sp1': [
            'cloud/clouds/dimensiondata_test.py::DimensionDataTestCase::test_avail_sizes',
        ],
        'sles12sp2': [
            'cloud/clouds/dimensiondata_test.py::DimensionDataTestCase::test_avail_sizes',
        ],
        '2016.11.4': [
            '*network_test.py::NetworkTestCase::test_host_to_ips',
        ],
        'sles15': [
            'utils/test_args.py::ArgsTestCase::test_argspec_report', # Bad tests, fixed at https://github.com/saltstack/salt/pull/52852
        ],
        'ubuntu1604': [
            'utils/test_args.py::ArgsTestCase::test_argspec_report', # Bad tests, fixed at https://github.com/saltstack/salt/pull/52852
            # Needs investigation. Setting them to xfail to have a "new green start" on March 19th
            # https://github.com/SUSE/spacewalk/issues/14263
            'modules/test_saltsupport.py::SaltSupportModuleTestCase::test_sync_specified_archive_not_found_failure',
            'modules/test_saltsupport.py::SaltSupportModuleTestCase::test_sync_last_picked_archive_not_found_failure',
            'modules/test_aptpkg.py::AptPkgTestCase::test_add_repo_key_failed',
            'cli/test_support.py::ProfileIntegrityTestCase::test_users_template_profile',
            'cli/test_support.py::ProfileIntegrityTestCase::test_non_template_profiles_parseable',
            'cli/test_support.py::ProfileIntegrityTestCase::test_jobs_trace_template_profile',
            'transport/test_zeromq.py::PubServerChannel::test_issue_36469_tcp',
        ],
        'ubuntu1804': [
            'utils/test_args.py::ArgsTestCase::test_argspec_report', # Bad tests, fixed at https://github.com/saltstack/salt/pull/52852
            # Needs investigation. Setting them to xfail to have a "new green start" on March 19th
            # https://github.com/SUSE/spacewalk/issues/14263
            'modules/test_saltsupport.py::SaltSupportModuleTestCase::test_sync_specified_archive_not_found_failure',
            'modules/test_saltsupport.py::SaltSupportModuleTestCase::test_sync_last_picked_archive_not_found_failure',
            'modules/test_aptpkg.py::AptPkgTestCase::test_add_repo_key_failed',
            'cli/test_support.py::ProfileIntegrityTestCase::test_users_template_profile',
            'cli/test_support.py::ProfileIntegrityTestCase::test_non_template_profiles_parseable',
            'cli/test_support.py::ProfileIntegrityTestCase::test_jobs_trace_template_profile',
            # These also need investigation, setting to xfail for a green start for 3002.2
            'transport/test_tcp.py::ClearReqTestCases::test_badload',
            'transport/test_tcp.py::ClearReqTestCases::test_basic',
            'transport/test_tcp.py::ClearReqTestCases::test_normalization',
            'transport/test_tcp.py::AESReqTestCases::test_basic',
            'transport/test_tcp.py::AESReqTestCases::test_normalization',
            'transport/test_zeromq.py::ClearReqTestCases::test_badload',
            'transport/test_zeromq.py::ClearReqTestCases::test_basic',
            'transport/test_zeromq.py::ClearReqTestCases::test_normalization',
        ],
        # ip_addrs() needs to be mocked for deterministic tests
        "opensuse151": ['pytests/unit/utils/test_minions.py'],
        "opensuse152": ['pytests/unit/utils/test_minions.py'],
        "opensuse153": ['pytests/unit/utils/test_minions.py'],
    }
}


KNOWN_ISSUES = {
    'integration': KNOWN_ISSUES_INTEGRATION,
    'unit': KNOWN_ISSUES_UNIT
}


def get_list(config, name):
    version = os.environ.get('DISTRO')
    flavor = os.environ.get('FLAVOR')
    tests_type = config.getini('tests_type')
    assert name in ['ignore_list', 'xfail_list']
    result = (
        KNOWN_ISSUES[tests_type][name].get('common', []) +
        KNOWN_ISSUES[tests_type][name].get(flavor, []) +
        KNOWN_ISSUES[tests_type][name].get(version, []) +
        KNOWN_ISSUES[tests_type][name].get(
            '{0}/{1}'.format(version, flavor), []) +
        KNOWN_ISSUES[tests_type][name].get(
            '{0}/{1}'.format(version, config.salt_version), []) +
        KNOWN_ISSUES[tests_type][name].get(config.salt_version, [])
    )
    return ['*%s*' % it for it in result]


def pytest_ignore_collect(path, config):
    return any(map(path.fnmatch, config.ignore_list))


def pytest_itemcollected(item):
    matcher = partial(fnmatch, item.nodeid)
    if any(map(matcher, item.config.xfail_list)):
        item.add_marker(pytest.mark.xfail, "Xfailed by toaster")
    elif any(map(matcher, item.config.ignore_list)):
        item.add_marker(pytest.mark.skip, "Ignore by toaster")
