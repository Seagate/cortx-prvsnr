# Framework of Southbound API
Southbound API is an interface expected by Provisioner. This interface provides a mechanism for interaction across Provisioner and interacting components.
The basis of such interactions would be a setup.yaml file that is maintained by each participating component under `/opt/seagate/cortx/<component>/conf/setup.yaml`

This file has the following structure:
```
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
    script: null
    args: null
  config:
    script: null
    args: null
  init:
    script: null
    args: null
  test:
    script: null
    args: null
  reset:
    script: null
    args: null
  backup:
    files:
      - /var/lib/my_file1
      - /etc/component/my_config_file2
  sync:                               # No doc: avoid using this
    files:
      - /var/lib/my_file1
      - /etc/component/my_config_file2
  refresh_config:
    script: null
    args: null

support_bundle:
  - /opt/seagate/cortx/provisioner/cli/provisioner-bundler
```

## setup.yaml File Sections Explained
* **The root node (\<component\>)**: is the name of the component. This has to be same as the name mentioned in `/opt/seagate/cortx/<component>/conf/setup.yaml`.  
* **Sub-sections** for <**component**> root node:  
    * **post_install**:  This section is called after the component rpm is installed from config .sls  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  
    * **config**: This section shall follow the post_install and is intended to allow components to update/adjust the configurations according to local environments  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  
    * **init**: This section has a purpose to initialize the component (i.e. mark it ready) for service. This shall config the config stage  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  
    * **test**: This section should have scripts to validate the state of the component, i.e. to ensure component sanity post deployment. This would be post the **init** stage  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  
    * **reset**: A reset script is supposed to cleanup the component after itself for any critical/non-critical data before the component package (rpm) is uninstalled  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  
    * **backup**: Backup section is slightly different as here we don't execute any scripts. However, Provisioner would use a mechanism define in custom execution module sync.py to backup files (and restore when required)  
        **files**: The list of files to be backed-up. The same list would be used as a reference for restore. If a file specified in this list is missed, it would be skipped with a warning in `/var/log/seagate/provisioner/salt-minion.log`.  
    * **refresh_config**: Refresh config section would be used by the component to correct any deviations in config file detected by the component, which would have a detrimental impact on the service provided by the component  
        **script**:  Script to be executed provided by component pertaining to this section  
        **args**:  A list of arguments (in yaml format) for the script mentioned against **script**  

**support_bundle**: This is a special section used by [cortx-manager](https://github.com/Seagate/cortx-manager) to locate the script provided by the component for generating component specific support_bundle  

**NOTE**: Any section left blank in `setup.yaml` would be neglected. `refresh_config` as of the time of writing is only called in `deploy_replacement` script on request by the components.  