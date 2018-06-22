#! /usr/bin/python

from invoke import task

@task(help={'suse': "run susetests"})
def leap15(c, suse=False):
    """
    run leap15 tests
    """
    if suse:
        print("suse")
    print("Building!")
    c.run("docker pull dmaiocchi/leap15-salt-toaster")
