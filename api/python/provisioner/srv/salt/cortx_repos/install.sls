#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

# TODO TEST

{% if "RedHat" in grains['os'] %}

setup_yum_salt_repo:
  file.managed:
    - name: /etc/yum.repos.d/saltstack.repo
    - source: salt://cortx_repos/files/etc/yum.repos.d/saltstack.repo
    - keep_source: True
    - backup: minion
    - onchanges_in:
      - clean_yum_salt_repo_metadata
      - import_yum_salt_repo_key

# TODO IMPROVE look for specific salt module instead of cmd.run
clean_yum_salt_repo_metadata:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="saltstack" clean metadata

{% else %}

setup_yum_repos:
  file.recurse:
    - name: /etc/yum.repos.d
    - source: salt://cortx_repos/files/etc/yum.repos.d
    - clean: True
    - keep_source: True
    - maxdepth: 0
    - backup: minion
    - onchanges_in:
      - clean_yum_cache
      - import_yum_salt_repo_key

# TODO IMPROVE look for specific salt module instead of cmd.run
clean_yum_cache:
  cmd.run:
    - name: yum clean expire-cache && rm -rf /var/cache/yum

{% endif %}

#epel_release_installed:
#  pkg.installed:
#    - name: epel-release

# TODO IMPROVE look for specific salt module instead of cmd.run
# TODO IMPROVE a temporary fix since later version (2019.2.1) is buggy
# (https://repo.saltstack.com/#rhel, instructions for minor releases centos7 py3)
import_yum_salt_repo_key:
  cmd.run:
    - name: rpm --import https://archive.repo.saltstack.com/py3/redhat/7/x86_64/archive/2019.2.0/SALTSTACK-GPG-KEY.pub
