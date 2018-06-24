#! /usr/bin/python

from invoke import task

@task(help={'suse': "run susetests"})
def leap15(c, suse=True, saltstack.unit=False, saltstack.integration=False):
    """
    run leap15 tests
    """
    c.run("docker pull dmaiocchi/leap15-salt-toaster")
    if suse:
        c.run("sandbox/bin/pytest -c ./configs/suse.tests/leap15/products.cfg ./tests")
    if saltstack.unit:
        c.run("sandbox/bin/pytest -c ./configs/saltstack.unit/leap15/products.cfg ./tests")
    if saltstac.integration:
        c.run("sandbox/bin/pytest -c ./configs/saltstack.integration/leap15/products.cfg ./tests")
