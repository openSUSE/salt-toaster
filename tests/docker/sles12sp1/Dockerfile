# Container used to run salt tests focusing on SUSE Manager use cases
#
# NAME                  toaster-sles12sp1
# VERSION               0

FROM registry.mgr.suse.de/suma-3.0-salt-sle12sp1
MAINTAINER Mihai Dincă: "mdinca@suse.com"


EXPOSE 4444

# Add the repositories
ADD add_repositories.sh /root/add_repositories.sh
RUN /root/add_repositories.sh

# Install the packages required to run the cobbler tests
ADD add_packages.sh /root/add_packages.sh
RUN /root/add_packages.sh

ADD bin/install_salt.sh /root/install_salt.sh
RUN /root/install_salt.sh
