import pytest


pytestmark = pytest.mark.usefixtures("minion")


@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [
            {
                "config": {
                    "container__config__salt_config__extra_configs": {
                        "cp_push": {
                            "file_recv": True
                        }
                    }
                },
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


POLICY_NAME = "scap-yast2sec"
POLICY = "/usr/share/openscap/{0}-xccdf.xml".format(POLICY_NAME)
PROFILE = "Default"


def test_openscap_xccdf_eval_success(minion):
    result = minion.salt_call(
        "--local", "openscap.xccdf 'eval --profile {0} {1}'".format(PROFILE, POLICY))
    assert result['success'] is True
    assert result['upload_dir']


def test_openscap_xccdf_eval_uploads_files(master, minion):
    result = master.salt(
        minion['id'], "openscap.xccdf 'eval --profile {0} {1}'".format(PROFILE, POLICY)
    )[minion['id']]
    files = filter(
        lambda f: f,
        master['container'].run(
            'ls /var/cache/salt/master/minions/{0}/files/{1}'.format(
                minion['id'], result['upload_dir'])
        ).split('\n')
    )
    assert 'results.xml' in files
    assert 'report.html' in files
    assert "{0}-oval.xml.result.xml".format(POLICY_NAME) in files
    assert '%2Fusr%2Fshare%2Fopenscap%2Fcpe%2Fopenscap-cpe-oval.xml.result.xml' in files


def test_openscap_xccdf_eval_removes_files_from_minion(master, minion):
    result = minion.salt_call(
        "openscap.xccdf 'eval --profile {0} {1}'".format(PROFILE, POLICY))
    expect = minion.salt_call(
        '--local', "file.directory_exists {0}".format(result['upload_dir']))
    assert expect is False
