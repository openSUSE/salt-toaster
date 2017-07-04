import pytest
import time
import json
from functools import partial

@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [
            {
                "config": {
                    'container__config__salt_config__sls': {
                        'saltapi': 'tests/sls/saltapi.sls',
                    },
                    "container__config__salt_config__extra_configs": {
                        "rosters_paths": {
                            "rosters": ['/salt-toaster/tests/data/good.roster'],
                        },
                        "salt_api_config": {
                            "rest_cherrypy": {
                                "port": 9080,
                                "host": "127.0.0.1",
                                "collect_stats": False,
                                "disable_ssl": True,
                            },
                            "external_auth": {
                                "auto": {
                                    "admin": ['.*', '@wheel', '@runner', '@jobs']
                                },
                            },
                        },
                    },
                },
                "minions": [{"config": {}}]
            }
        ]
    }


@pytest.fixture()
def salt_api_running(master):
    master['container'].run('salt-call --local pkg.refresh_db')
    master['container'].run('salt-call --local pkg.install salt-api')
    master['container'].run('salt-api -d')


@pytest.mark.xfail
def test_roster_sshapi_disabled(master, salt_api_running):
    '''
    Test if Salt API is not accepting custom roster.
    '''
    # create a malicious roster
    with open('/tmp/malicious.roster', 'w') as rst:
        for line in ['exploit:\n',
                     "  host: '$(touch /tmp/malicious.file)'\n",
                     '  user: dummy\n',
                     '  passwd: dummy\n']:
            rst.write(line)

    # call malicious roster
    out = run("curl -sS localhost:9080/run -H 'Accept: application/x-yaml' -d client='ssh' "
              "-d tgt='exploit' -d fun='test.ping' -d roster_file='/tmp/malicious.roster'")
    assert '- {}' in out


@pytest.fixture()
def expected(request, minion):
    expectations = {
        'salt-2017.7': json.dumps({"return": [{minion['id']: False}]}),
        'default': json.dumps({"return": [{}]})
    }
    tags = set(request.config.getini('TAGS'))
    intersection = tags.intersection(set(expectations)) or {'default'}
    return expectations[intersection.pop()]


def test_timeout_and_gather_job_timeout(request, master, salt_api_running, minion, expected):
    minion['container'].disconnect()
    request.addfinalizer(minion['container'].connect)

    # Giving some time to salt-api to starting up.
    time.sleep(3)

    pre_ping_time = time.time()
    cmd = (
        'curl -sS localhost:9080/run -H "Content-type: application/json"'
        ' -d \'[{"client": "local", "tgt": "*", "fun": "test.ping", '
        '"timeout": 3, "gather_job_timeout": 1, "username": "admin", '
        '"password": "admin", "eauth": "auto"}]\''
    )
    api_ret = master['container'].run(cmd)
    post_ping_time = time.time()

    assert api_ret == expected
    assert (post_ping_time - pre_ping_time) < 10
