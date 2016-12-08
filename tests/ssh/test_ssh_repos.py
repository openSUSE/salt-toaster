import pytest


@pytest.mark.tags('sles')
def test_pkg_owner(setup):
    '''
    Test pkg.owner
    '''
    #assert master.salt_ssh("pkg.owner /etc/zypp") == 'libzypp'


@pytest.mark.tags('sles')
def test_pkg_list_products(master):
    '''
    List test products
    '''
    products = master.salt_ssh("pkg.list_products")
    for prod in products:
        if prod['productline'] == 'sles':
            assert prod['productline'] == 'sles'
            assert prod['name'] in ['SLES', 'SUSE_SLES']  # SLE12 says "SLES" and SLE11 says "SUSE_SLES"
            assert prod['vendor'] == 'SUSE'
            assert prod['isbase']
            assert prod['installed']
            break
        else:
            raise Exception("Product not found")


@pytest.mark.tags('sles', 'leap')
def test_pkg_search(master):
    assert 'test-package-zypper' in master.salt_ssh("pkg.search test-package")


@pytest.mark.tags('sles', 'leap')
def test_pkg_repo_sles(master):
    assert master.salt_ssh('pkg.list_repos')['testpackages']['enabled']


def test_pkg_mod_repo(master):
    assert not master.salt_ssh('pkg.mod_repo testpackages enabled=false')['enabled']
    assert master.salt_ssh('pkg.mod_repo testpackages enabled=true')['enabled']


@pytest.mark.tags('sles', 'leap')
def test_pkg_del_repo_sles(master):
    msg = "Repository 'testpackages' has been removed."
    out = master.salt_ssh('pkg.del_repo testpackages')
    assert out['message'] == msg
    assert out['testpackages']

