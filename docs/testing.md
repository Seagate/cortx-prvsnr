# Testing Using Docker

**Table of Contents**

- [Installation](#Installation)
  - [Docker configuration](#docker-configuration)
  - [Docker on Fedora 32/33](#docker-on-fedora-33)
  - [Python configuration](#python-configuration)
- [Basic Docker commands](#basic-docker-commands)    


## Installation

#### Docker configuration

The base Docker installation methods for popular Linux distributions are listed here:
	https://docs.docker.com/engine/install/

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
<summary>2. As docker doesn't support **CGroups2**, enable old **CGroups**</summary>

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
<summary>5. Add your user to **docker** group to run docker without **sudo**</summary>

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

#### Python configuration

- Install `python3.6` package in system using your distributive package manager tool: **apt**, **dnf**, **yum**, etc.

- Clone/Update the `cortx-prvsnr` repository

- Create the Python virtual environment using `venv` module

  ```bash
  cd /path/to/cortx-prvsnr
  python3.6 -m venv ./venv
  ```

  :warning: NOTE: For more details about Python virtual environment see
  https://docs.python.org/3.6/library/venv.html

- Install provisioner API to `venv`: 

  ```bash
  pip install -e api/python[test]
  ```

- Start the docker environment creation

  ```bash
  pytest test/build_helpers -k test_build_setup_env -s --root-passwd root --nodes-num 1
  ```

  <details>
  <summary>The command above will create the docker container and will have the following output</summary>
    
  ```
    ========================================================================================= test session starts ==========================================================================================
    platform linux -- Python 3.6.13, pytest-5.1.1, py-1.10.0, pluggy-0.13.1
    rootdir: /home/fdmitry/Work/cortx-prvsnr, inifile: pytest.ini
    plugins: timeout-1.3.4, testinfra-3.1.0, mock-3.1.0, xdist-1.29.0, forked-1.3.0
    timeout: 7200.0s
    timeout method: signal
    timeout func_only: False
    collected 1 item                                                                                                                                                                                       
    
    test/build_helpers/test_build_env.py::test_build_setup_env Host srvnode-1
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

    Possible options (you may check them using `pytest test/build_helpers --help`, `custom options` part)
    - `--docker-mount-dev` to mount `/dev` into containers (necessary if you need to mount ISO inside a container)
    - `--root-passwd <STR>` to set a root password for initial ssh access
    - `--nodes-num <INT>` number of nodes, currently it can be from 1 to 3


- You may set up a provisioner inside the container using the local source mode

  ```bash
  provisioner setup_provisioner --source local --logfile --logfile-filename ./setup.log --console-formatter full srvnode-1:172.17.0.2
  ```

  **:warning:** NOTE: For **srvnode-1**, **srvnode-2**, etc. parameter values use the **Hostname** output from previous step

#### TBD: Test other types of sources.
#### TBD: Update with examples for multi node setups with HA mode enabled.

## Basic Docker commands

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