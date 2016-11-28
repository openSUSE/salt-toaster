import re
import json
import pytest
import requests
from jsonschema import validate


pytestmark = pytest.mark.usefixtures(
    'setup',
    'terminal_stream',
    'api_stream',
    'fire_event',
    'fetch_events_from_terminal',
    'fetch_events_from_api')


MANUAL_TAG = 'my/event/test'


SCHEMA_DEFINITIONS = {
    "manual_event": {
        "type": "object",
        "properties": {
            "_stamp": {"type": "string"},
            "id": {"type": "string"},
            "cmd": {"type": "string"},
            "tag": {"type": "string"},
            "data": {
                "type": "object",
                "properties": {
                    "__pub_fun": {"type": "string"},
                    "__pub_jid": {"type": "string"},
                    "__pub_pid": {"type": "number"},
                    "__pub_tgt": {"type": "string"},
                    "test": {"type": "boolean"}
                },
                "required": [
                    "__pub_fun",
                    "__pub_jid",
                    "__pub_pid",
                    "__pub_tgt",
                    "test"]
            }
        },
        "required": [
            "_stamp",
            "id",
            "cmd",
            "tag",
            "data"]
    },
    "manual_event_wrapped_in_data": {
        "type": "object",
        "properties": {
            "tag": {"type": "string"},
            "data": {
                "$ref": "#/definitions/manual_event"
            }
        },
        "required": ["tag", "data"]
    },
    "beacon_event": {
        "type": "object",
        "properties": {
            "_stamp": {"type": "string"},
            "tag": {"type": "string"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": ["string", "number"]},
                    "1m": {"type": ["string", "number"]},
                    "5m": {"type": ["string", "number"]},
                    "15m": {"type": ["string", "number"]}
                },
                "required": [
                    "id",
                    "1m",
                    "5m",
                    "15m"]
            }
        },
        "required": [
            "_stamp",
            "tag",
            "data"]
    },
    "beacon_event_wrapped_in_data": {
        "type": "object",
        "properties": {
            "_stamp": {"type": "string"},
            "tag": {"type": "string"},
            "data": {"$ref": "#/definitions/beacon_event"},
        },
        "required": ["tag", "data"]
    }
}


@pytest.fixture(scope='module')
def module_config(request):
    return {'masters': [
        {
            'config': {
                'container__config__salt_config__extra_configs': {
                    'external_auth': {
                        'external_auth': {
                            "auto": {
                                "saltuser": [
                                    {"*": [
                                        ".*",
                                        "@wheel",
                                        "@runner",
                                        "@jobs"
                                    ]}
                                ]
                            }
                        }
                    },
                    'cherrypy': {
                        'rest_cherrypy': {'port': 8000, 'disable_ssl': True}
                    }
                },
                'container__config__salt_config__apply_states': {
                    'top': 'tests/sls/master/top.sls',
                    'salt-api': 'tests/sls/master/salt-api.sls',
                }
            },
            'minions': [
                {
                    'config': {
                        'container__config__salt_config__extra_configs': {
                            'beacons': {
                                'beacons': {
                                    'load': {
                                        'emitatstartup': True,
                                        '1m': [0.0, 2.0],
                                        '5m': [0.0, 1.5],
                                        '15m': [0.1, 1.0]
                                    }
                                }
                            }
                        }
                    }
                }
            ]}
    ]}


@pytest.fixture(scope="module")
def ip(setup):
    config, initconfig = setup
    return config['masters'][0]['fixture']['container']['ip']


@pytest.fixture(scope="module")
def token(setup, ip):
    config, initconfig = setup
    response = requests.post(
        'http://{}:8000/login'.format(ip),
        headers={"Accept": "application/json"},
        json={'username': 'saltuser', 'password': 'saltuser', 'eauth': 'auto'}
    )
    response.raise_for_status()
    return response.json()['return'][0]['token']


@pytest.fixture(scope="module")
def api_stream(ip, token):
    stream = requests.get(
        'http://{}:8000/events?token={}'.format(ip, token), stream=True)
    return stream.iter_lines(decode_unicode=True)


@pytest.fixture(scope="module")
def terminal_stream(setup):
    config, initconfig = setup
    master = config['masters'][0]
    stream = master['fixture']['container'].run(
        'salt-run --out json -l quiet state.event', stream=True)
    return stream


@pytest.fixture()
def fire_event(setup):
    config, initconfig = setup
    container = config['masters'][0]['minions'][0]['fixture']['container']
    container.run(
        'salt-call -l quiet event.send "{}" "{}"'.format(
            MANUAL_TAG, '{test: True}'))


@pytest.fixture(scope="module")
def manual_event():
    return dict()


@pytest.fixture(scope="module")
def beacon_event():
    return dict()


def fetch_events(stream, patterns):
    out = dict(manual=None, beacon=None)
    for item in stream:
        for key, pattern in patterns.items():
            match = re.match(pattern, item)
            if match:
                out[key] = json.loads(match.group('data'))
        if all(out.values()):
            break
    return out


@pytest.fixture(scope="module")
def fetch_events_from_terminal(terminal_stream):
    patterns = dict(
        manual='(?:^%s\\t)(?P<data>{.+}$)' % MANUAL_TAG,
        beacon='(?:^salt/beacon/.+?/load/\t)(?P<data>{.+}$)')
    return fetch_events(terminal_stream, patterns)


@pytest.fixture(scope="module")
def fetch_events_from_api(api_stream):
    patterns = dict(
        manual='(?:^data:\\s+)(?P<data>{.+?"%s".+}$)' % MANUAL_TAG,
        beacon='(?:^data:\\s+)(?P<data>{.+?"salt/beacon/.+?/load/".+}$)')
    return fetch_events(api_stream, patterns)


def pytest_generate_tests(metafunc):
    sources = ['from-terminal', 'from-api']
    metafunc.parametrize('events', sources, indirect=['events'], ids=sources)


@pytest.fixture()
def events(request, fetch_events_from_api, fetch_events_from_terminal):
    return {
        'from-terminal': fetch_events_from_terminal,
        'from-api': fetch_events_from_api}[request.param]


@pytest.mark.tags('sles')
def test_manual_events(events):
    schema = {
        "definitions": SCHEMA_DEFINITIONS,
        "oneOf": [
            {"$ref": "#/definitions/manual_event"},
            {"$ref": "#/definitions/manual_event_wrapped_in_data"},
        ]
    }
    validate(events['manual'], schema)


@pytest.mark.tags('sles')
def test_beacon_events(events):
    schema = {
        "definitions": SCHEMA_DEFINITIONS,
        "oneOf": [
            {"$ref": "#/definitions/beacon_event"},
            {"$ref": "#/definitions/beacon_event_wrapped_in_data"},
        ]
    }
    validate(events['beacon'], schema)
