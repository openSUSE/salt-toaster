# -*- coding: utf-8 -*-
import pytest
import os


@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                "config": {
                    "container__config__salt_config__extra_configs": {
                        "yaml_utf8": {
                            'file_roots': {
                                'base': ["/etc/salt/masterless"]
                            },
                            # "yaml_utf8": True
                        },
                    },
                    "container__config__salt_config__sls": [
                        "tests/sls/unicode/top.sls",
                        "tests/sls/unicode/unicode.sls",
                        "tests/sls/unicode/unicode1.sls",
                        "tests/sls/unicode/unicode2.sls",
                        "tests/sls/unicode/cocös.txt",
                    ]
                },
                'minions': [{'config': {}}]
            }
        ]
    }


def test_state_apply_unicode_sls(setup, master, minion):
    master.salt_call('--local state.apply', 'unicode')
    # master.salt_call('--local state.apply', 'unicode1')
    # master.salt_call('--local state.apply', 'unicode2')
    # master.salt(minion['id'], 'state.apply', 'unicode')
    # master.salt(minion['id'], 'state.apply', 'unicode1')
    # master.salt(minion['id'], 'state.apply', 'unicode2')
