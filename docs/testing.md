# Provisioner Testing Approaches

**Table of Contents**

- [Python environment preparation](#python-environment-preparation)
- [Static validation](#static-validation)
  - [Python code](#python-code)
    - [flake8](#flake8)
    - [Codacy tools](#codacy-tools)
      - [Bandit](#bandit)
      - [Prospector](#prospector)
      - [Pylint](#pylint)
      - [Radon](#radon)
- [Unit testing](#unit-testing)
- [Integration testing](#integration-testing)
  - [Testing with Docker](#testing-with-Docker)
    - [Docker configuration](#docker-configuration)
    - [Docker on Fedora 32/33](#docker-on-fedora-33)
    - [Docker test helpers](#Docker-test-helpers)
      - [Docker environment creation](#docker-environment-creation)
      - [Building provisioner packages](#building-provisioner-packages)
      - [Building testing bundles](#building-testing-bundles)
    - [Integration test cases](#Integration-test-cases)
      - [Provisioner setup](#Provisioner-setup)
- [Appendix](#appendix)
  - [Basic Docker commands](#basic-docker-commands)


## Python environment preparation

- Install `python3.6` package in system using your distributive package manager tool: **apt**, **dnf**, **yum**, etc.

- Clone/Update the `cortx-prvsnr` repository

- Create the Python virtual environment using `venv` module

  ```bash
  cd /path/to/cortx-prvsnr
  python3.6 -m venv ./venv
  ```

  :warning: NOTE: For more details about Python virtual environment see
  https://docs.python.org/3.6/library/venv.html

- Activate created Python environment

  ```bash
  source venv/bin/activate
  ```

- Install provisioner API to `venv` with extras for testing:

  ```bash
  pip install -e api/python[test]
  ```

- [Optionally] Install provisioner API to `venv` with extras for Codacy testing tools:

  ```bash
  pip install -e api/python[codacy]
  ```

## Static validation

There are multiple tools that help to do static validation to ensure
the quality of the changes and alignment with code style accepted
in the repository.

### Python code

#### flake8

We encourage a contributor to use [flake8](https://flake8.pycqa.org/en/latest/)
before pushing any changes:

To test everything:

```
flake8
```

To test specific files / directories:

```
flake8 path/to/directory_or_file
```

#### Codacy tools

GitHub repository is configured to validate each PR using [codacy](https://docs.codacy.com/).
Codacy does the static analysis, checks duplications and complexity.
For python it [uses](https://docs.codacy.com/getting-started/supported-languages-and-tools/) the
following tools:

  - static analysis:
    [Bandit](https://github.com/PyCQA/bandit),
    [Prospector](https://github.com/landscapeio/prospector2),
    [Pylint](https://www.pylint.org/)
  - duplications: [PMD CPD](https://pmd.github.io/pmd/pmd_userdocs_cpd.html)
  - complexity: [Radon](https://github.com/rubik/radon)

All these tools (except [PMD CPD](https://pmd.github.io/pmd/pmd_userdocs_cpd.html)
which is not a python one) would be availble once you
[installed API](#python-environment-preparation) with testing dependnecies.

So in case your PR fails Codacy verification you may check the issues locally.

**Note.** In case GitHub Codacy issue is not reproduced locally then it
likely means you have a different version and/or different
settings for a tool. In such cases Codacy report is the source of truth.

##### Bandit

```bash
# test specific file
bandit path/to/file.py

# test the directory (project) recursively
bandit -r path/to/directory
```

More [examples](https://github.com/PyCQA/bandit#usage).

##### Prospector

```bash
prospector path/to/directory_or_file
```

##### Pylint

```bash
pylint path/to/directory_or_file
```

More running [examples](http://pylint.pycqa.org/en/latest/user_guide/run.html).

##### Radon

```bash
# compute Cyclomatic Complexity, calculate the average complexity at the end and
# print only results with a complexity rank of C or worse
radon cc path/to/directory_or_file -a -nc
```

More [examples](https://radon.readthedocs.io/en/latest/commandline.html#the-cc-command).

## Unit testing

**TBD**

## Integration testing

### Testing with Docker

#### Docker configuration

The base Docker installation methods for popular Linux distributions are listed
[here](https://docs.docker.com/engine/install/).

To run Docker commands without **sudo**, add your user to **docker** group

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

After that command, re-login/re-connect to your terminal or VM console.

:warning: NOTE: for more information about post-installation steps, please,
visit the [official page](https://docs.docker.com/engine/install/linux-postinstall/).

#### Docker on Fedora 33

Docker is not supported by **Fedora 33** officially. You can use the following method (Moby based approach):

<details>
<summary>1. Delete the old version of docker (if it was installed)</summary>

```bash
sudo dnf remove docker-*
sudo dnf config-manager --disable docker-*
```
</details>


<details>
<summary>2. As docker doesn't support <strong>CGroups2</strong>, enable old <strong>CGroups</strong>
</summary>

```bash
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"
```
</details>


<details>
<summary>3. Configure firewall</summary>

```bash
sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0
sudo firewall-cmd --permanent --zone=FedoraWorkstation --add-masquerade
```
</details>


<details>
<summary>4. Install Moby (an open-source project created by Docker)</summary>

   ```bash
   sudo dnf install moby-engine docker-compose
   sudo systemctl enable docker
   ```
</details>


<details>
<summary>5. Add your user to <strong>docker</strong> group to run docker without <strong>sudo</strong></summary>

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```
</details>


<details>
<summary>6. Restart your computer</summary>

```bash
sudo reboot
```
</details>


<details>
<summary>7. To test your installation you need running the following command</summary>

```bash
sudo docker run hello-world
```
</details>

#### Docker test helpers

##### Building provisioner packages

  ```bash
  pytest test/build_helpers/build_prvsnr_pkgs
  ```

  The command above will create provisioner packages (core and api) in the current directory.

  You may check the full list of options using `pytest test/build_helpers/build_prvsnr_pkgs --help`
  (`custom options` part):

  - `--build-version=STR` release version (source version). Note. ignored for
     api package, to set version for package please edit
     `api/python/provisioner/__metadata__.py`
  - `--build-pkg-version=INT` package version (release tag),
     should be greater or  equal 1
  - `--build-output=DIR` path to directory to output

##### Building testing bundles

  ```bash
  pytest test/build_helpers/build_bundles
  ```

  The command above will create three bundles in the current directory.

  They would respect the structure of CORTX distributions for deployment and upgrade
  but include mocks for CORTX packages instead of real ones. Non CORTX yum repositories
  inside would be just empty.

  Optionally you may pack inside real repositories of EPEL-7, SaltStack and
  GlusterFS along with provisioner release packages that are distributed inside
  official CORTX bundles. For that you need to download a bundle locally
  and run the following command:

  ```bash
  pytest test/build_helpers/build_bundles --build-orig-single-iso <path-to-official-bundle>
  ```

  Also you may pack custom provisioner packages available locally:

  ```bash
  pytest test/build_helpers/build_bundles \
            --build-prvsnr-pkg=<path-to-prvsnr-pkg> \
            --build-prvsnr-api-pkg=<path-to-prvsnr-api-pkg>
  ```

  For the full list of available options please run
  `pytest test/build_helpers/build_bundles --help` (`custom options` part):

  - `--build-type=TYPE` type of the bundle [choices: deploy-cortx, deploy-bundle, upgrade, all]
  - `--build-version=STR` version of the release, ignored if 'all' type is used
  - `--build-output=BUILD_OUTPUT` path to file or directory to output
  - `--build-orig-single-iso=BUILD_ORIG_SINGLE_ISO` original CORTX single ISO for partial use
  - `--build-prvsnr-pkg=BUILD_PRVSNR_PKG PATH` to provisioner core rpm package
  - `--build-prvsnr-api-pkg=BUILD_PRVSNR_API_PKG PATH` to provisioner API rpm package


##### Docker environment creation

  ```bash
  pytest test/build_helpers/build_env -s --root-passwd root --nodes-num 1
  ```

  The command above will create the docker container.

  <details>
  <summary>It will result with the following example output</summary>

  ```
    ========================================================================================= test session starts ==========================================================================================
    platform linux -- Python 3.6.13, pytest-5.1.1, py-1.10.0, pluggy-0.13.1
    rootdir: /home/fdmitry/Work/cortx-prvsnr, inifile: pytest.ini
    plugins: timeout-1.3.4, testinfra-3.1.0, mock-3.1.0, xdist-1.29.0, forked-1.3.0
    timeout: 7200.0s
    timeout method: signal
    timeout func_only: False
    collected 1 item

    test/build_helpers/build_env/test_build_env.py::test_build_setup_env Host srvnode-1
      Hostname 172.17.0.2
      Port 22
      User root
      UserKnownHostsFile /dev/null
      StrictHostKeyChecking no
      IdentityFile /tmp/pytest-of-fdmitry/pytest-10/id_rsa.test
      IdentitiesOnly yes
      LogLevel FATAL

  ```
  </details>

  You may check the full list of options using `pytest test/build_helpers/build_env --help`
  (`custom options` part):

    - `--docker-mount-dev` to mount `/dev` into containers (necessary if you need to mount ISO inside a container)
    - `--root-passwd <STR>` to set a root password for initial ssh access
    - `--nodes-num <INT>` number of nodes, currently it can be from 1 to 6

#### Integration test cases

##### Provisioner setup

You may set up a provisioner inside the container using the local source mode

```bash
provisioner setup_provisioner --source local --logfile --logfile-filename ./setup.log --console-formatter full srvnode-1:172.17.0.2
```

**:warning:** NOTE: For **srvnode-1**, **srvnode-2**, etc. parameter values use the **Hostname** output from previous step

**TBD: Test other types of sources.**

**TBD: Update with examples for multi node setups with HA mode enabled.**

## Appendix

### Basic Docker commands

* List docker containers by their ID

  ```bash
  docker ps
  ```

  :warning:NOTE: Use `docker ps --help`  to see all options

* Copy sources from host to docker container

  ```bash
  docker cp /PATH/TO/SOURCE <CONTAINER ID>:/DESTINATION/PATH
  ```

  :warning: NOTE: You can find `<CONTAINER ID>` from `docker ps` command output

* Enter to docker container (create the new Bash session)

  ```bash
  docker exec -it <CONTAINER ID> bash
  ```
