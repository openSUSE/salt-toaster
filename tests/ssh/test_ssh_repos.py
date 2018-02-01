import pytest


@pytest.mark.tags('sles')
def test_pkg_owner(setup):
    '''
    Test pkg.owner
    '''
    #assert master.salt_ssh("pkg.owner /etc/zypp") == 'libzypp'


@pytest.mark.tags('sles')
def test_pkg_list_products(master, container):
    '''
    List test products
    '''
    products = master.salt_ssh(container, "pkg.list_products")
    for prod in products:
        if prod['productline'] == 'sles':
            assert prod['productline'] == 'sles'
            assert prod['name'] in ['SLES', 'SUSE_SLES']  # SLE12 says "SLES" and SLE11 says "SUSE_SLES"
            assert 'SUSE' in prod['vendor']
            assert prod['isbase']
            assert prod['installed']
            break
        else:
            raise Exception("Product not found")


@pytest.mark.tags('sles', 'leap')
def test_pkg_search(master, container):
    assert 'test-package-zypper' in master.salt_ssh(container, "pkg.search test-package")


@pytest.mark.tags('sles', 'leap')
def test_pkg_repo_sles(master, container):
    assert master.salt_ssh(container, 'pkg.list_repos')['testpackages']['enabled']


@pytest.mark.tags('rhel')
def test_pkg_repo_rhel(master, container):
    '''
    Iterate over all available repos and at least one should be enabled.
    '''
    repos = master.salt_ssh(container, 'pkg.list_repos')
    assert [enabled for enabled in [repos[repo].get('enabled', 0) for repo in repos.keys()] if enabled]


@pytest.mark.tags('rhel')
def test_pkg_mod_repo_rhel(master, container):
    repo = master.salt_ssh(container, 'pkg.list_repos').keys()[0]

    res = master.salt_ssh(container, 'pkg.mod_repo {} enabled=0'.format(repo))
    assert not res[res.keys()[0]][repo]['enabled']

    res = master.salt_ssh(container, 'pkg.mod_repo {} enabled=1'.format(repo))
    assert res[res.keys()[0]][repo]['enabled']


@pytest.mark.tags('sles', 'leap')
def test_pkg_mod_repo_sles(master, container):
    assert not master.salt_ssh(container, 'pkg.mod_repo testpackages enabled=false')['enabled']
    assert master.salt_ssh(container, 'pkg.mod_repo testpackages enabled=true')['enabled']


@pytest.mark.tags('rhel')
def test_pkg_del_repo_rhel(master, container):
    repo = master.salt_ssh(container, 'pkg.list_repos').keys()[0]
    out = master.salt_ssh(container, 'pkg.del_repo {0}'.format(repo))
    assert '{0} has been removed'.format(repo) in out


@pytest.mark.tags('sles', 'leap')
def test_pkg_del_repo_sles(master, container):
    msg = "Repository 'testpackages' has been removed."
    out = master.salt_ssh(container, 'pkg.del_repo testpackages')
    assert out['message'] == msg
    assert out['testpackages']

