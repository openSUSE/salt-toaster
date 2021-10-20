# Salt Toaster: SUSE internal R&D setup

Additionally to the common setup, if you are inside SUSE R&D network, you have also access to the non-public
Salt Toaster images listed using the `list_targets` command, but you will require to perform some extra configuration
steps:

## Install SUSE CA Certificate

```bash
sudo zypper in ca-certificates
```

Then you need to download the registry certificate needed here:
`https://gitlab.suse.de/galaxy/infrastructure/raw/master/srv/salt/ca/certs/ca.cert.pem`

Save the certificate in `/usr/share/pki/trust/anchors` (openSUSE) or in `/usr/local/share/ca-certificates/` for
Debian systems

And run:

```bash
sudo update-ca-certificates
sudo systemctl restart docker
```

At least for Tumbleweed it might be enough to copy the certificate to `/etc/docker/certs.d/registry.mgr.suse.de/` and
then run:

```bash
sudo systemctl restart docker
```
