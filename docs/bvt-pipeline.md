:warning:
**This doc is out-of-date at the moment.


# Build Verification Testing Pipeline

The [pipeline](../devops/bvt/Jenkinsfile.bvt) automates new releases verification using
testing suite from [cortx-test](https://seagit.okla.seagate.com/eos/qa/eos-test/)
repository and logic of dynamic environment management provided by [testing suite](../test)
from the current repository.

The pipeline is set up here: <http://eos-jenkins.colo.seagate.com/job/eos-prvsnr-qa-bvt>

## Requirements

### Jenkins Server

- cleanWS plugin: <https://plugins.jenkins.io/ws-cleanup>
- junit plugin: <https://plugins.jenkins.io/junit>
- API token in Jenkins Credentials Store with type `Secret Text` and ID `eos-test-repo-api-token`

### Jenkins Agent

Please refer [here](https://github.com/Seagate/cortx-prvsnr#jenkins-agent).

## Configuration

The pipeline accepts the following parameters:

- `cortxRelease`: CORTX stack release to use as source for provisioner and CORTX stack components.
Default: `integration/centos-7.7.1908/last_successful`.
- `cortxTestRepoVersion`: version of the [cortx-test](https://seagit.okla.seagate.com/eos/qa/cortx-test/)
repository to use. Default: `release`.

## Artifacts

The pipeline stores the following artifacts on Jenkins server:

- junit test results (parsed by Jenkins [JUnit](https://plugins.jenkins.io/junit) plugin)
- bvt job logs `job.log`
- in case of failure only:
  - the whole bvt job results directory as `bvt.results.tgz`
  - journalctl output as `journalctl.out.txt`
  - output stream as `pytest.out.txt`
  - logs stream as `pytest.log`
