#! /usr/bin/python

from invoke import task

@task(help={'suse': "run susetests"})
def leap15(c, suse=False):
    """
    run leap15 tests
    """
    c.run("docker pull dmaiocchi/leap15-salt-toaster")
    if suse:
        c.run("sandbox/bin/pytest -c ./configs/suse.tests/leap15/products.cfg ./tests")
