# Provisioner CI/CD automation

## Table of Contents

*   [Overview](#overview)

*   [Pre-requisites](#pre-requisites)

    *   [docker installation](#docker-installation)

*   [Installation](#installation)

*   [Jenkins configuration automation](#jenkins-configuration-automation)

    *   [Jenkins Server](#jenkins-server)

        *   [Start the server](#start-the-server)
        *   [Initial run](#initial-run)
        *   [Server management](#server-management)
        *   [Additional configuration](#additional-configuration)
        *   [Server Command line reference](#server-command-line-reference)

    *   [Jenkins Agents](#jenkins-agents)

        *   [Build and start](#build-and-start)
        *   [Agent Management](#agent-management)
        *   [Agent Command line reference](#agent-command-line-reference)
        *   [Jenkins Agent Troubleshootings](#jenkins-agent-troubleshootings)

    *   [Provisioner Jobs on Jenkins](#provisioner-jobs-on-jenkins)

        *   [Jobs update](#jobs-update)
        *   [Jobs Command line reference](#jobs-command-line-reference)

## Overview

This python package provides `cortx-jenkins` CLI tool to build and run Jenkins
infrastracture along with automation for provisioner Jenkins jobs configuration.

It uses the following tools:

*   [docker](https://docs.docker.com/): both server and agents are run as docker containers
*   [JCasC](https://www.jenkins.io/projects/jcasc/) plugin: to automate Jenkins server configuration
*   [JJB](https://jenkins-job-builder.readthedocs.io/en/lates) tool/library: to automate Jenkins jobs configurations

## Pre-requisites

### docker installation

The following automates the steps from the
[official docker docs](https://docs.docker.com/engine/install/)
for Debian, Ubuntu and Centos:

```bash
sudo bash cortx_jenkins/agent/setup_docker.sh
```

## Installation

Run the following in activated python3 virtualenv

```bash
pip install devops/jenkins
```

You may also want to add `-e` to install in editable mode.

## Jenkins configuration automation

`cortx-jenkins` tool can be configured using a configuration file.

You may use [cortx-jenkins.toml.example](cortx_jenkins/cortx-jenkins.toml.example)
as a starting point for your configuration.

Alternatively you may dump the example using:

```bash
cortx-jenkins dump-config
```

It is in [TOML](https://github.com/toml-lang/toml) format.

It has few configuration sections:

*   `global`: common configuration
*   `server`: for server
*   `agent`: for agents
*   `jobs`: for jobs

Please check the example for the details regarding supported parameters.

### Jenkins Server

Base command: `cortx-jenkins server`.

Possible actions:

*   `create`: builds and starts server docker container
*   `start`/`stop`/`restart`/`remove`: to start/stop/restart/destroy server container

Options:

*   `--ssl-domain DOMAIN` will be used for self-signed certificate generation to support HTTPS
*   `--config PATH` path to a configuration file

Configuration:

*   `[global]`
    *   `url` Jenkins server url
    *   `username` Jenkins user with admin access
    *   `token` Jenkins user acess token

*   `[server]`:
    *   `smeeio_channel`: url to a [smee.io](https://smee.io) channel that can be used for integration with version control system (e.g. GitHub) to receieve payloads (push) even on a local Jenkins setup (**not for production**).
*   `[server.properties]`: a set of parameters for Jenkins global configuration

#### Start the server

The following command will build server container, run it and starts the server
configured accordingly to the provieded parameters (including plugins installation):

```bash
cortx-jenkins server create
```

In case of local setup Jenkins will be available at `https://localhost:8083/`.

#### Initial run

During the first run Jenkins will ask you to go through a few steps:

1.  to unlock the server using the admin initial password. You would be provided
    with a path on a server as an option and you can resolve the password as follows:

    ```bash
    docker exec -it cortx-prvsnr-jenkins cat <path>
    ```

2.  After that you would be prompted to specify the list of plugins.
    As long as the current logic takes care about that automatically you will likely
    want to close the window to skip that step. Alternatively you can choose
    `Select plugin to install` and unselect all using `None` and then `Install`.

3.  The next step will create first admin user, you would be able
    to specify credentials and other admin settings.

4.  The last step would be about Jenkins server url configuration.
    The default value will match one specified in configuration file.
    So you can leave that as-is.

#### Server management

A server is started as a docker container with name `cortx-prvsnr-jenkins`
and mounted volume `jenkins_home`.

To stop/start/restart a server you can use either `cortx-jenkins server`
subcommands or similar `docker` commands.

#### Additional configuration

Additional manual configuration of a running server is not considered
as a best choice.

If you need to adjust the configuration please consider to do:

*   to change existent parameters values: update your configuration file
*   to change the configuration scheme: update [server/jenkins.yaml.tmpl](cortx_jenkins/server/jenkins.yaml.tmpl)
*   to adjust a list of plugins: update [server/plugins.txt](cortx_jenkins/server/plugins.txt)

Once the change is ready you can rebuild the server:

```bash
cortx-jenkins server remove
cortx-jenkins server create
```

**Note**. The command above won't celanup but update an existent configuration.

In latter two cases please also consider to submit a patch to `cortx-prvsnr`
repository.

#### Server Command line reference

```bash
$ cortx-jenkins server --help
usage: cortx-jenkins server [-h] [-c PATH] [--ssl-domain domain]
                            {create,stop,start,restart,remove}

Jenkins server management

positional arguments:
  {create,stop,start,restart,remove}
                        server action to perform

optional arguments:
  -h, --help            show this help message and exit
  -c PATH, --config PATH
                        path to a file with cortx-jenkins config. Consider to
                        use `dump-config` command to dump an example to
                        standard output (default: cortx-jenkins.toml)
  --ssl-domain domain   server name protected by the SSL certificate (aka
                        Common Name or CN) (default: localhost
```

### Jenkins Agents

Jenkins agents are created as a docker containers.

**Assumption** Jenkins server has got a configured set
of persistent Java Web Start (aka JNLP)
[Jenkins agents](https://www.jenkins.io/projects/remoting/).

Base command: `cortx-jenkins agent`.

Possible actions are the same as for the server.

Options:

*   `--name NAME` optional name of a Jenkins agent to use for the connection.
*   `--config PATH` path to a configuration file
*   `--work-dir PATH` path to a Jenkins agent root directory, whould be writeable for the current user. Default is `/var/lib/jenkins`.

**Note** The options above make sense only for `create` action
where agent configuration takes places.

**Note** Jenkins agent root directory should exists, has write permissions
for the current user and match the server agent configuration.

Configuration:

*   `[global]`
    *   `ssl_verify`: can be set to `false` to turn off ssl verification for requests to a Jenkins server (e.g. in case of self-signed certificate is used)
*   `[agent]`: (optional, if not specified `[global]` settings are used)
    *   `url` Jenkins server url
    *   `username` Jenkins user with permissions to Configure, Connect and Disconnect agents.
    *   `token` Jenkins user acess token.

#### Build and start

Prepare a local directory that would be used as a mount point (docker binding)
for the agent and all its docker container siblings that might be created in
scope of pipeline docker container management routine (please use `sudo`
if needed):

```bash
mkdir -p /var/lib/jenkins
chown $USER:$USER /var/lib/jenkins
```

Run:

```bash
cortx-jenkins agent create
```

Jenkins agent will automatically connect the server and become online.

#### Agent Management

An agent is started as a docker container with name `cortx-prvsnr-jenkins-agent`
and mounted local directory as a working directory for a jenkins agent.

To stop/start/restart an agent you can use either `cortx-jenkins agent` subcommands
or similar `docker` commands.

#### Agent Command line reference

```bash
$ cortx-jenkins agent --help
usage: cortx-jenkins agent [-h] [-c PATH] [-n NAME] [-w PATH]
                           {create,stop,start,restart,remove}

Jenkins agent management

positional arguments:
  {create,stop,start,restart,remove}
                        agent action to perform

optional arguments:
  -h, --help            show this help message and exit
  -c PATH, --config PATH
                        path to a file with cortx-jenkins config. Consider to
                        use `dump-config` command to dump an example to
                        standard output (default: cortx-jenkins.toml)
  -n NAME, --name NAME  an agent name to use for connection. Detected
                        automatically if not specified. (default: None)
  -w PATH, --work-dir PATH
                        path to a directory to use as a jenkins root, will be
                        bind to a container. Should be writeable for the
                        current user (default: /var/lib/jenkins)
```

#### Jenkins Agent Troubleshootings

In case you encounter an error like

> remote agent is not yet configured (no secret and/or working dir is set):
> No such file or directory

You will likely need to verify the jenkins credentials you set.

### Provisioner Jobs on Jenkins

Jenkins jobs are managed using [JJB](https://jenkins-job-builder.readthedocs.io/en/lates)
which provides python API as well:

Base command: `cortx-jenkins jobs`.

Possible actions:

*   `update`: to create or update jobs
*   `delete`: to remove jobs

Options:

*   `--config PATH` path to a configuration file
*   `--jjb-args JJB_ARGS` a string that would be passed to JJB
    as running arguments. Please check
    [JJB docs](https://jenkins-job-builder.readthedocs.io/en/latest/execution.html#command-reference)
    for possible options.

Configuration:

*   JJB run configuration:
    *   `[global]`: specifies `url`, `username` and `token` as explained above.
    *   `[jobs]`: that block would passed directly to JJB tool. Please refer to
        [the docs](https://jenkins-job-builder.readthedocs.io/en/latest/execution.html#configuration-file)
        for more details.
*   jobs configuration:
    *   you can either change [defaults](./cortx_jenkins/jobs/defaults.yaml)
        or update [jobs definitions](./cortx_jenkins/jobs/cortx-prvsnr/cortx-prvsnr-jobs.yaml)

#### Jobs update

**Note.** you will likely want to set a proper github access token credential id
`github_credentials_id` in [defaults](./cortx_jenkins/jobs/defaults.yaml).

```bash
cortx-jenkins jobs update
```

#### Jobs Command line reference

```bash
$ cortx-jenkins jobs --help
usage: cortx-jenkins jobs [-h] [-c PATH] [--jjb-args JJB_ARGS] {update,delete}

Jenkins jobs management

positional arguments:
  {update,delete}       jobs action to perform

optional arguments:
  -h, --help            show this help message and exit
  -c PATH, --config PATH
                        path to a file with cortx-jenkins config. Consider to
                        use `dump-config` command to dump an example to
                        standard output (default: cortx-jenkins.toml)
  --jjb-args JJB_ARGS   Additional JJB arguments (default: None)
```
