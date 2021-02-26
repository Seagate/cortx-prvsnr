# Testing Using Docker

**Table of Contents**

- [Installation](#Installation)
  - [Docker configuration](#docker-configuration)
  - [Python configuration](#python-configuration)
- [Basic Docker commands](#basic-docker-commands)    


## Installation

#### Docker configuration

The base Docker installation methods for popular Linux distributions are listed here:
	https://docs.docker.com/engine/install/

Docker is not supported by **Fedora 33** officially. On my host system I used the following method (Moby based approach):

1. Delete the old version of docker (if it was installed)

   ```bash
   sudo dnf remove docker-*
   sudo dnf config-manager --disable docker-*
   ```

2. As docker doesn't support **CGroups2**, enable old **CGroups**

   ```bash
   sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"
   ```

3. Configure firewall

   ```bash
   sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0
   sudo firewall-cmd --permanent --zone=FedoraWorkstation --add-masquerade
   ```

4. Install Moby (an open-source project created by Docker)

   ```bash
   sudo dnf install moby-engine docker-compose
   sudo systemctl enable docker
   ```

5. Add your user to **docker** group to run docker without **sudo**

   ```bash
   sudo groupadd docker
   sudo usermod -aG docker $USER
   ```

6. Restart your computer

   ```bash
   sudo reboot
   ```

7. To test your installation you need running the following command

   ```bash
   sudo docker run hello-world
   ```

#### Python configuration

- Install `python3.6` package in system using your distributive package manager tool: **apt**, **dnf**, **yum**, etc.

- Clone/Update the `cortx-prvsnr` repository

- Create the Python virtual environment using `venv` module

  ```bash
  cd /path/to/cortx-prvsnr
  python3.6 -m venv ./venv
  ```

- Install provisioner API to `venv`: 

  ```bash
  pip install -e api/python[test]
  ```

- Start the docker environment creation

  ```bash
  pytest test/build_helpers -k test_build_setup_env -s --root-passwd root --nodes-num 1
  ```

  The command above will create the docker container and will have the following output

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

- Install provisioner API to created docker container

  ```bash
  provisioner setup_provisioner --source local --logfile --logfile-filename ./setup.log --console-formatter full srvnode-1:172.17.0.2
  ```

  **:warning:** NOTE: For **srvnode-1**, **srvnode-2**, etc. parameter values use the **Hostname** output from previous step

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