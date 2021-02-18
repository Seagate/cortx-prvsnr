# Quick Guide For Mock environment deployment

Sometimes it is desired to test provisioner logic without any actual CORTX SW stack
deployment to save time and focus on provisioner own logic avoiding any other
components issues and integration difficulties.

For that cases mocked deployment should help. It comes with the following mocks and features:

- dummy component packages which includes only `setup.yaml` (provisioner mini specification)
- `setup.yaml` itself is a very simple spec that just logs (registers) all the calls from provisioner
  (pushes logs to `/tmp/mock.log`)
- automated logic can build various deployment and upgrade artifacts (all as an ISO or a directory):
  - cortx yum repository
  - single repo bundle that might be used for a deployment
  - upgrade bundle that might be used for an upgrade routine verification

# Commands

## Mocking the environment

```bash
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx
```

That would:

- build and setup a repo with mocked CORTX packages
- install the packages

## Building upgrade bundle

```bash
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.build_upgrade
```

That would create a bundle release directory (along with ISO) with CORTX packages repo inside.

By default it will be located at `/var/lib/seagate/cortx/provisioner/local/cortx_repos/upgrade_mock_2.0.0`.

The output directory might be configured using an inline pillar, e.g.:

```bash
salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.build_upgrade pillar='{"inline": {"upgrade_repo_dir": "/tmp/upgrade"}}'
```
