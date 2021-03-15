import os
import glob
import pytest
from functools import partial
from fnmatch import fnmatch
from saltrepoinspect import get_salt_version


def pytest_addoption(parser):
    parser.addini("tests_type", help="Type of the tests being run", default='unit')


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
        'sles15sp2': [
            'transport/test_zeromq.py', # Leaks memory on SLE15SP2
            'transport/test_tcp.py',
        ],
    },
    'xfail_list': {
        'common': [
            # fixed in saltstack/develop
            # https://github.com/saltstack/salt/commit/7427e192baeccfee69b4887fe0c630a1afb38730#diff-3b5d15bc59b82fc8d4b15f819babf4faR70
            'test_core.py::CoreGrainsTestCase::test_parse_etc_os_release',
            'test_core.py::CoreGrainsTestCase::test_fqdns_socket_error',
            'test_x509.py::X509TestCase::test_private_func__parse_subject',
            'test_zypper.py::ZypperTestCase::test_list_pkgs_with_attr',
            'test_zfs.py::ZfsUtilsTestCase::test_property_data_zpool',

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
            'EtcdModTestCase',
            'ConfTest::test_conf_master_sample_is_commented',  # this is not passing because we have custom config by default (user "salt")
            'test_cmdmod.py::CMDMODTestCase::test_run',

            'fileserver/test_roots.py::RootsTest::test_symlink_list',
            'modules/test_cmdmod.py::CMDMODTestCase::test_run',  # test too slow
            '*test_reactor.py::TestReactor::test_reactions',
            '*test_reactor.py::TestReactor::test_list_reactors',
            '*test_yumpkg.py::YumTestCase::test_list_pkgs_with_attr',
            '*test_local_cache.py::Local_CacheTest::test_clean_old_jobs',
            '*test_local_cache.py::Local_CacheTest::test_not_clean_new_jobs',
            '*test_jinja.py::TestCustomExtensions::test_http_query',
            '*test_conf.py::ConfTest::test_conf_master_sample_is_commented',

            # After switch to M2Crypto
            'modules/test_x509.py::X509TestCase::test_create_crl', # No OpenSSL available
            'modules/test_x509.py::X509TestCase::test_revoke_certificate_with_crl', # No OpenSSL available

            # Fails due to the async batch changes
            'transport/test_ipc.py::IPCMessagePubSubCase::test_multi_client_reading',

            # Needs investigation. Setting them to xfail to have a "new green start" on March 12th
            # https://github.com/SUSE/spacewalk/issues/14263
            'utils/test_jinja.py::TestCustomExtensions::test_json_query',
            'utils/test_data.py::DataTestCase::test_json_query',
            'states/test_syslog_ng.py::SyslogNGTestCase::test_started_state_generate_valid_cli_command',
            'states/test_pip_state.py::PipStateTest::test_install_requirements_parsing',
            'states/test_network.py::NetworkTestCase::test_managed',
            'modules/test_zypperpkg.py::ZypperTestCase::test_upgrade_success',
            'modules/test_zypperpkg.py::ZypperTestCase::test_search_not_found',
            'modules/test_zypperpkg.py::ZypperTestCase::test_add_repo_key_path',
            'modules/test_state.py::StateTestCase::test_show_sls',
            'modules/test_serverdensity_device.py::ServerdensityDeviceTestCase::test_create',
            'modules/test_redismod.py::RedismodTestCase::test_shutdown',
            'modules/test_redismod.py::RedismodTestCase::test_ping',
            'modules/test_netscaler.py::NetscalerTestCase::test_service_enable',
            'modules/test_netscaler.py::NetscalerTestCase::test_service_disable',
            'modules/test_keystone.py::KeystoneTestCase::test_user_get',
            'modules/test_keystone.py::KeystoneTestCase::test_user_create',
            'modules/test_keystone.py::KeystoneTestCase::test_tenant_get',
            'modules/test_keystone.py::KeystoneTestCase::test_tenant_create',
            'modules/test_keystone.py::KeystoneTestCase::test_role_get',
            'modules/test_dpkg_lowpkg.py::DpkgTestCase::test_info',
            'modules/test_cron.py::PsTestCase::test_list_tab',
            'modules/test_aptpkg.py::AptPkgTestCase::test_info_installed_attr_without_status',
            'grains/test_core.py::CoreGrainsTestCase::test_fqdn_return',
            'grains/test_core.py::CoreGrainsTestCase::test_fqdn4_empty',
            'cloud/clouds/test_ec2.py::EC2TestCase::test_termination_protection_exception',
            'cloud/clouds/test_ec2.py::EC2TestCase::test_termination_protection',
            'cli/test_batch_async.py::AsyncBatchTestCase::test_batch_start_on_gather_job_timeout',
            'cli/test_batch_async.py::AsyncBatchTestCase::test_batch_start_on_batch_presence_ping_timeout',
            'cli/test_batch_async.py::AsyncBatchTestCase::test_batch_next',
            'cli/test_batch_async.py::AsyncBatchTestCase::test_batch_close_safe',
            'cli/test_batch_async.py::AsyncBatchTestCase::test_batch__del__',
            'beacons/test_cert_info.py::CertInfoBeaconTestCase::test_cert_information',
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
        ],
        'ubuntu1804': [
            'utils/test_args.py::ArgsTestCase::test_argspec_report', # Bad tests, fixed at https://github.com/saltstack/salt/pull/52852
        ],
    }
}


KNOWN_ISSUES = {
    'integration': KNOWN_ISSUES_INTEGRATION,
    'unit': KNOWN_ISSUES_UNIT
}


def get_list(config, name):
    version = os.environ.get('VERSION')
    flavor = os.environ.get('FLAVOR')
    tests_type = config.getini('tests_type')
    assert name in ['ignore_list', 'xfail_list']
    result = (
        (KNOWN_ISSUES[tests_type][name].get('common') or []) +
        (KNOWN_ISSUES[tests_type][name].get(flavor) or []) +
        (KNOWN_ISSUES[tests_type][name].get(version) or []) +
        (KNOWN_ISSUES[tests_type][name].get(
            '{0}/{1}'.format(version, flavor)) or []) +
        (KNOWN_ISSUES[tests_type][name].get(
            '{0}/{1}'.format(version, config.salt_version)) or []) +
        (KNOWN_ISSUES[tests_type][name].get(config.salt_version) or [])
    )
    return ['*%s*' % it for it in result]


def pytest_ignore_collect(path, config):
    return any(map(path.fnmatch, config.ignore_list))


def pytest_itemcollected(item):
    matcher = partial(fnmatch, item.nodeid)
    if any(map(matcher, item.config.xfail_list)):
        item.addExpectedFailure(item.parent, None)
    elif any(map(matcher, item.config.ignore_list)):
        item.addSkip(item.parent, None)


def pytest_configure(config):
    config.salt_version = get_salt_version(
        os.environ.get('VERSION'), os.environ.get('FLAVOR'))
    config.xfail_list = get_list(config, 'xfail_list')
    config.ignore_list = get_list(config, 'ignore_list')
    tests_path = '{0}/salt-*/tests'.format(os.environ.get('ROOT_MOUNTPOINT'))
    os.sys.path.extend(glob.glob(tests_path))

def pytest_collection_modifyitems(session, config, items):
    items = items.reverse()

@pytest.fixture(scope="session")
def test_daemon(add_options, request):
    from integration import TestDaemon
    return TestDaemon(request.instance)


@pytest.fixture(scope="session")
def transplant_configs(test_daemon):
    test_daemon.transplant_configs(transport='zeromq')


@pytest.fixture(scope="session")
def add_options(request):
    from tests.runtests import SaltTestsuiteParser
    parser = SaltTestsuiteParser([])
    request.instance.options, args = parser.parse_args([])


@pytest.fixture(scope="session")
def salt_test_daemon(transplant_configs, test_daemon, request):
    finalizer = partial(test_daemon.__exit__, None, None, None)
    request.addfinalizer(finalizer)
    test_daemon.__enter__()
