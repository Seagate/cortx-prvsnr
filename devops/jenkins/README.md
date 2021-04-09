# Provisioner CI/CD automation

**Table of Contents**


## Jenkins configuration automation

### Jenkins Server

TBD:
 - overview
 - JCasC plugin

#### Summary

```bash
cp server/jenkins_inputs.tmpl server/jenkins_inputs

# edit server/jenkins_inputs

build_jenkins.sh
```

#### Configuration parameters

There are few exposed parameters listed in [server/jenkins_inputs.tmpl](server/jenkins_inputs.tmpl).
Please:
  - copy [server/jenkins_inputs.tmpl](server/jenkins_inputs.tmpl) to `server/jenkins_inputs`
  - define parameters inside it

#### Build and start

Run:

```bash
build_jenkins.sh 
```

:warning: Note. The script doesn't consider any command line arguments for the moment and
it expects `server/jenkins_inputs` script to be in place.


#### Initial run

During the first run Jenkins will ask you to go through a few steps:

1. to unlock the server using the admin initial password. You would be provided
   with a path on a server as an option and you can resolve the password as follows:

    ```bash
    docker exec -it cortx-prvsnr-jenkins cat <path>
    ```
1. After that you would be prompted to specify the list of plugins.
   As long as the current logic takes care about that automatically you will likely
   want to skip that step by choosing `Select plugin to install`, unselect all using `None`
   and then `Install`.

1. The next step will create first admin user, you would be able to specify credentials
   and other admin settings.

1. The last step would be about Jenkins server url configuration.
   The default value will match one specified in configuration file.
   So you can leave that as-is.

#### Server management

A server is started as a docker container with name `cortx-prvsnr-jenkins`
and mounted volume `jenkins_home`.

Currenty server UI is available only as `http://localhost:8080`.

To stop/start/restart a server you can use accordant `docker` commands.

To remove the container:


```bash
docker stop cortx-prvsnr-jenkins
docker rm cortx-prvsnr-jenkins
# OR
docker rm -f cortx-prvsnr-jenkins
```

#### Additional configuration

Additional manual configuration of a running server is not considered as a best choice.

If you need to adjust the configuration please consider to do:
- update `server/jenkins_inputs` to change existent parameters values
- update [server/jenkins.yaml.tmpl](server/jenkins.yaml.tmpl) if you need to
  change the configuration
- update [server/jenkins_inputs.tmpl](server/jenkins_inputs.tmpl) as well
  if you need to expose a new parameter

Once the change is ready you can stop jenkins and re-run
[devops/jenkins/build_jenkins.sh](devops/jenkins/build_jenkins.sh).

In case of configuration changes (latter two cases) you might also want
to submit a patch to `cortx-prvsnr` repository.

### Jenkins Agents

*TBD*
 - overview
 - Java Web Start (aka JNLP) Jenkins agents

#### Summary

```bash
cp agent/credentials.tmpl agent/credentials

# edit agent/credentials

mkdir -p /var/lib/jenkins
chown $USER:$USER /var/lib/jenkins

build_jenkins_agent.sh <jenkins-url> <agent-name>
```

#### Configuration

Please:
  - copy [agent/credentials.tmpl](agent/credentials.tmpl) to `agent/credentials`
  - and specify jenkins user credentials there

*TBD* what permission a user should have to

#### Build and start

Prepare a local directory that would be used as a mount point (docker binding)
for the agent and all its docker container siblings that might be created in
scope of pipeline docker container management routine (please use `sudo` if needed):

*TBD* verify
```bash
mkdir -p /var/lib/jenkins
chown $USER:$USER /var/lib/jenkins
```

Run:

```bash
build_jenkins_agent.sh <jenkins-url> <agent-name>
```

where:
 - `<jenkins-url>` is a server url accessible for a dockerized jenkins agent
 - `<agent-name>` is a name of an agent already configured (but not attached)
    on the server as a JNLP one

Jenkins agent will automatically connect the server and become online.

#### Agent Management

An agent is started as a docker container with name `cortx-prvsnr-jenkins-agent`
and mounted local directory as a working directory for a jenkins agent.

To stop/start/restart a server you can use accordant `docker` commands.

To remove the container:

```bash
docker stop cortx-prvsnr-jenkins-agent
docker rm cortx-prvsnr-jenkins-agent
# OR
docker rm -f cortx-prvsnr-jenkins-agent
```

#### Command line reference

```bash
./build_jenkins_agent.sh -h
Usage: ./build_jenkins_agent.sh [options] jenkins-url agent-name

Options:
  -h,  --help               print this help and exit
  -c,  --creds-file FILE    path to a file with jenkins credentials
                            at the first line USER:APITOKEN,
                                default: <path-to-repo>/devops/jenkins/agent/credentials
  -w,  --work-dir DIR       path to a directory to use as a jenkins root,
                            will be bind to a container. Should be writeable
                            for the current user.
                                default: (detected automatically)
  -v,  --verbose            be more verbose
```

#### Jenkins Agent Troubleshootings

In case you encounter an error like

> remote agent is not yet configured (no secret and/or working dir is set): No such file or directory

You will likely need to verify the jenkins credentials you set.


### Provisioner Jobs on Jenkins

*TBD*

#### Summary

```bash
# activate python3 virtual env and run
pip install -r jobs/requirements.txt

# OR
# pip3 install --user -r jobs/requirements.txt

cp jobs/jenkins.ini.example jobs/jenkins.ini

# edit jobs/jenkins.ini

jenkins-jobs --conf jobs/jenkins.ini update -r jobs
```
