# Framework of Southbound API

Table of contents:

- [Framework of Southbound API](#framework-of-southbound-api)
  - [Summary of Southbound API](#summary-of-southbound-api)
  - [`setup.yaml` File Sections Explained](#setupyaml-file-sections-explained)


## Summary of Southbound API

Southbound API is an interface expected by Provisioner. This interface provides a mechanism for interaction across Provisioner and interacting components.

The basis of such interactions would be a `setup.yaml` file that is maintained by each participating component under `/opt/seagate/cortx/<component>/conf/setup.yaml`.

This file has the following structure:

```yaml
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

<component>:
  post_install:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup post_install
    args: --config <URL>
    
  config:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup config
    args: --config <URL>
    
  init:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup init
    args: --config <URL>
    
  test:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup test
    args: --config <URL>
    
  reset:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup reset
    args: --config <URL>
    
  cleanup:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup cleanup
    args: --config <URL>
    
  backup:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup backup
    args: --location <URL>
    
  restore:
    cmd: /opt/seagate/cortx/<component>/bin/<component>_setup restore
    args: --location <URL>

support_bundle:
  - /opt/seagate/cortx/provisioner/cli/provisioner-bundler
```

## `setup.yaml` File Sections Explained

* **The root node (`<component>`)**: is the name of the component. This has to be same as the name mentioned in `/opt/seagate/cortx/<component>/conf/setup.yaml`.

Each of the sub-sections (unless mentioned explicitly) will have the following parameters:

  * `cmd`:  Command to be run provided by component pertaining to this section.
  * `args`:  A list of arguments (in YAML format) to be passed to the script.
  * `--config <URL>`:  Source URL with cluster info
  * `--location <URL>`:  Target URL as specific end-point to backup/restore config info

Supported **Sub-sections** for `<component>` root node are listed below:

* `post_install`:  This section is called after the component rpm is installed from config `.sls`.

* `config`: This section shall follow the post_install and is intended to allow components to update/adjust the configurations according to local environments.

* `init`: This section has a purpose to initialize the component (i.e. mark it ready) for service. This shall complete the configuration of the component.  This would be post the `config` stage.

* `test`: This section should have scripts to validate the state of the component, i.e. to ensure component sanity post deployment. This would be post the `init` stage.

* `reset`: A reset script is supposed to cleanup the component after itself for any critical/non-critical data before the component package (rpm) is uninstalled.

* `cleanup`: Cleanup section would be used by the component to correct any deviations in config file detected by the component, which would have a detrimental impact on the service provided by the component.

* `backup`: This section is useful to save component specific state and configuration information at specific location URL (Custom endpoint). The backed config will be helpful to recover saved state in case of any detrimental situation and replay same configuration on multiple nodes.

* `restore`: This section is useful to restore component specific state and config information from specific location URL (Custom endpoint). The restored config will be helpful to recover saved state in case of any detrimental situation, provide debugging ability and replay configuration. 

`support_bundle`: This is a special section used by [`cortx-manager`](https://github.com/Seagate/cortx-manager) to locate the script provided by the component for generating component specific support_bundle.

**NOTE**: Any section left blank in `setup.yaml` would be neglected. `cleanup` as of the time of writing is only called in `deploy_replacement` script on request by the components.
