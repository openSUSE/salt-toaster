import time
import json
import pytest
import requests
from jsonschema import validate


pytestmark = pytest.mark.usefixtures(
    'setup', 'terminal_stream', 'api_stream', 'fire_event')


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


@pytest.fixture()
def event_tag(request, setup):
    config, initconfig = setup
    minion = config['masters'][0]['minions'][0]['fixture']
    return request.param.format(minion['id'])


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


@pytest.fixture()
def api_stream(ip, token):
    stream = requests.get(
        'http://{}:8000/events?token={}'.format(ip, token), stream=True)
    time.sleep(1)
    return stream


@pytest.fixture()
def terminal_stream(setup, event_tag):
    config, initconfig = setup
    master = config['masters'][0]
    stream = master['fixture']['container'].run(
        'salt-run --out json -l quiet state.event tagmatch="{}" count=1'.format(
            event_tag),
        stream=True
    )
    time.sleep(1)
    return stream


@pytest.fixture()
def fire_event(setup, api_stream):
    config, initconfig = setup
    container = config['masters'][0]['minions'][0]['fixture']['container']
    container.run(
        'salt-call -l quiet event.send "my/event/test" "{}"'.format(
            '{test: True}'))


@pytest.fixture()
def term_item(terminal_stream, event_tag):
    return json.loads(
        terminal_stream.next().replace('{}\t'.format(event_tag), ''))


@pytest.fixture()
def api_item(api_stream, event_tag):
    for item in api_stream.iter_lines(decode_unicode=True):
        if '"tag": "{}"'.format(event_tag) in item:
            if item.startswith('data: '):
                return json.loads(item.replace('data: ', ''))


@pytest.fixture()
def item(request, term_item, api_item):
    return {
        'from-terminal': term_item,
        'from-api': api_item
    }[request.param]


def pytest_generate_tests(metafunc):
    event_tag = {
        "test_manual_events": "my/event/test",
        "test_beacon_events": "salt/beacon/{}/load/"
    }[metafunc.function.func_name]
    sources = ['from-terminal', 'from-api']
    metafunc.parametrize(
        'event_tag, item',
        zip([event_tag]*2, sources),
        indirect=['event_tag', 'item'],
        ids=sources)


def test_manual_events(event_tag, item):
    schema = {
        "definitions": SCHEMA_DEFINITIONS,
        "oneOf": [
            {"$ref": "#/definitions/manual_event"},
            {"$ref": "#/definitions/manual_event_wrapped_in_data"},
        ]
    }
    validate(item, schema)


def test_beacon_events(event_tag, item):
    schema = {
        "definitions": SCHEMA_DEFINITIONS,
        "oneOf": [
            {"$ref": "#/definitions/beacon_event"},
            {"$ref": "#/definitions/beacon_event_wrapped_in_data"},
        ]
    }
    validate(item, schema)
