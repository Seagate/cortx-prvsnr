# Mocked CORTX Environment Deployment

Sometimes it is desired to test provisioner logic without any actual CORTX SW stack
deployment to save time and focus on provisioner own logic avoiding any other
components issues and integration difficulties.

For that cases mocked deployment should help. It comes with the following mocks and features:

- placeholder component packages which includes only `setup.yaml` (provisioner mini specification)
- `setup.yaml` itself is a very simple spec that just logs (registers) all the calls from provisioner
  (pushes logs to `/tmp/mock.log`)
- automated logic can build various deployment and upgrade artifacts (as an ISO or a directory):
  - cortx yum repository
  - singlerepo bundle that might be used for a deployment
  - upgrade bundle that might be used for an upgrade routine verification

# SaltStack states

There is a set of SaltStack states that can be applied to:
- mock a system
- build an upgrade bundle

## Mocking the environment

```bash
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx
```

That would:

- build and setup a repository with mocked CORTX packages
- install the packages

## Building upgrade bundle

```bash
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.build_upgrade
```

That would create a bundle release directory (along with ISO) with CORTX packages repository inside.

By default it will be located at `/var/lib/seagate/cortx/provisioner/local/cortx_repos/upgrade_mock_2.1.0`.

The output directory might be configured using an inline pillar, e.g.:

```bash
salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.build_upgrade \
    pillar='{"inline": {"upgrade_repo_dir": "/tmp/cortx-upgrade"}}'
```

# CLI

Under the hood the states above use [buildbundle.sh](srv/components/misc_pkgs/mocks/cortx/files/scripts/buildbundle.sh) script.

**Note**. Once provisioner is installed on a system the script is available as
`/opt/seagate/cortx/provisioner/srv/components/misc_pkgs/mocks/cortx/files/scripts/buildbundle.sh`.

It comes with the following usage help:

```bash
Usage: srv/components/misc_pkgs/mocks/cortx/files/scripts/buildbundle.sh [options]

Builds different types of CORTX distribution.

The type of a distribution, release version and output directory
can be configured.

If location of an original Cortx single repo image is specified
(using '--orig-iso') then EPEL-7, SaltStack and GlusterFS repositories
along with provisioner release packages would be copied from the ISO
to a new bundle.

Custom provisioner packages might be packed inside a bundle using
'--prvsnr-pkg' and '--prvsnr-api-pkg' options.

Finally if '--gen-iso' is specified then an ISO file is generated as well.

Options:
  -h,  --help                   print this help and exit
  -i,  --orig-iso FILE          original ISO for partial use,
                                    default:
  -o,  --out-dir DIR            output dir,
                                    default: .
  -r,  --cortx-ver              cortx release version,
                                    default: 2.0.0
  -t,  --out-type               output type. Possible values: {deploy-cortx|deploy-single|upgrade}
                                    default: deploy-cortx,
  -v,  --verbose                be more verbose
       --gen-iso                generate ISO
       --prvsnr-pkg FILE        provisioner package location
                                    default:
       --prvsnr-api-pkg FILE    provisioner api package location
                                    default:
```

Where output types are:
- `deploy-cortx`: a plain repository of CORTX SW packages
- `deploy-single`: a bundle disctribution that includes a set of directories
with yum repositories along with one for python index similar to a single repo disribution
used for deployment
- `upgrade`: an upgrade bundle, the structure is the same as for the `deploy-single` but also includes
a directory `os` with a yum repository inside
