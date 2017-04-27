import os

TIME_LIMIT = 120
WHEEL_CONFIG = {
    'user': 'apiuser',
    'password': 'linux'
}
GITLAB_AUTH = os.environ['GITLAB_AUTH']
DOCKER_CONTEXT="https://{0}@gitlab.suse.de/mdinca/toaster-docker-support.git#dev:docker".format(GITLAB_AUTH)
