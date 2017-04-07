import pytest
import time

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


@pytest.mark.xfail
def test_roster_sshapi_disabled(master):
    '''
    Test if Salt API is not accepting custom roster.
    '''
    run = master['container'].run
    run('salt-call --local pkg.refresh_db')
    run('salt-call --local pkg.install salt-api,curl')
    run('salt-api -d')

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


def test_timeout_and_gather_job_timeout(master, minion):
    master_run = master['container'].run
    master_run('salt-call --local pkg.refresh_db')
    master_run('salt-call --local pkg.install pkgs=\'["salt-api", "curl"]\'')
    master_run('salt-api -d')

    # Killing salt-minion process to get an unreachable minion
    minion['container'].run("pkill -9 salt-minion")
    # Giving some time to salt-api to starting up.
    time.sleep(3)

    pre_ping_time = time.time()
    api_ret = master_run('curl -sS localhost:9080/run -H "Content-type: application/json"'
                         ' -d \'[{"client": "local", "tgt": "*", "fun": "test.ping", '
                         '"timeout": 3, "gather_job_timeout": 1, "username": "admin", '
                         '"password": "admin", "eauth": "auto"}]\'')
    post_ping_time = time.time()

    # Starting salt-minion process again
    minion['container'].run("rcsalt-minion start")
    assert api_ret == '{"return": [{}]}'
    assert (post_ping_time - pre_ping_time) <= 6
