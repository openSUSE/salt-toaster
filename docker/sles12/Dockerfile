# Container used to run salt tests focusing on SUSE Manager use cases
#
# NAME                  toaster-sles12
# VERSION               1.0.0

FROM registry.mgr.suse.de/suma-3.0-salt-sle12
MAINTAINER Mihai Dincă: "mdinca@suse.com"

# Add the repositories
ADD add_repositories.sh /root/add_repositories.sh
RUN /root/add_repositories.sh

# Install the packages required to run the cobbler tests
ADD add_packages.sh /root/add_packages.sh
RUN /root/add_packages.sh

ADD install_salt.sh /root/install_salt.sh
RUN /root/install_salt.sh

ADD unpack_salt.sh /root/unpack_salt.sh
RUN /root/unpack_salt.sh
