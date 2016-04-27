# salt-toaster

## Run with defaults:
```bash
git clone https://github.com/dincamihai/salt-toaster.git
cd salt-toaster
make
```

## Examples

### Run docker shell in specific local image
```bash
make docker_shell DOCKER_IMAGE=toaster-sles12sp1
```

### Run docker shell in specific repository image
```bash
make docker_shell DOCKER_IMAGE=suma-docker-registry.suse.de/toaster-sles12sp1
```

### Run docker shell in repository image based on version
```bash
make docker_shell VERSION=sles12sp1
```
