# salt-toaster

Build images for salt-toaster

## Setup

The setup is pretty typical for small Python projects. Just clone the
repository, create a virtual environment, activate it and install the dependencies.

If you choose a different name for your virtual environment, you need to specify
it later as `VENV` when you use `make`.
``` sh
git clone https://gitlab.suse.de/galaxy/toaster-docker-support.git
cd toaster-docker-support
python3 -m venv sandbox
echo "*" > sandbox/.gitignore
. sandbox/bin/activate
python -m pip install -r images/requirements.txt
```

## Description

There are predefined flavors of salt packages plus a `devel` flavor.
The predefined flavors are packages served from OBS, see the (incomplete) list below:

 - [products](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products/salt)
 - [products:testing](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:testing/salt)
 - [products:next](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:next/salt)
 - [products:next:testing](https://build.opensuse.org/package/show/systemsmanagement:saltstack:products:next:testing/salt)

The `devel` flavor means:
1. archive `SALT_REPO` and push it to container:/salt/src/salt-devel
2. install Salt using `pip install -e /salt/src/salt-devel`

This allows testing Salt from a local repository.

Example (run in `salt-toaster` folder):
``` sh
make docker_shell DISTRO=sles12sp2 FLAVOR=devel SALT_REPO=/home/store/repositories/salt NOPULL=true
```

## Generate docker files

### Generate all files

The following will generate all flavors for all distros.
``` sh
python generate.py --all
```

### Generate for one or more specific distro(s)

The following will generate *all flavors* for *all specified* distros. 
``` sh
python generate.py --distro sle15 
# these aliases also work
python generate.py --distros sle15 sle15sp2
python generate.py -d sle15
```

### Generate for one or more specific flavor(s)

The following will generate the *specified flavors* for *all distros*. 
``` sh
python generate.py --flavor products 
# these aliases also work
python generate.py --flavors products products-testing
python generate.py -f products
```

### Generate for one or more specific flavor-distro combination

The following will generate each *specified flavor* for each *specified distro*.
``` sh
python generate.py --flavor products products-testing --distros sle15 sle15sp2
```

### Generate for one or more specific distro and flavor=devel

The devel flavor uses `BASE_FLAVOR` to install dependencies.
``` sh
BASE_FLAVOR=products-testing python generate.py --distro sles15 --flavor devel
```

## Buildin New Images

### Downloading the wheel packages

``` sh
pip wheel --wheel-dir=./docker/wheels -r docker/docker-requirements.txt
```

### Docker Build

`make` is used to invoke a Python script that triggers the "`docker build`". 
``` sh
make build_image DISTRO=sles15sp2 FLAVOR=products
```

If you named your virtual environment something other than `sandbox`, you can
pass it to `make` using `VENV`
``` sh
make build_image DISTRO=sles15sp2 FLAVOR=products VENV=venv
```

Devel images require a `SALT_REPO` parameter.
``` sh
make build_image DISTRO=sles15sp2 FLAVOR=devel SALT_REPO=/path/to/local/salt/repo
```



## Salt Toaster Usage

See [salt-toaster readme](https://github.com/openSUSE/salt-toaster/blob/master/README.adoc).

