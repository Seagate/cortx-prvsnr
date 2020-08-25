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

# TODO IMPROVE EOS-8473 move to pillar to make configurable
{% set install_dir = '/opt/seagate/cortx/provisioner' %}
{% set source = salt['pillar.get']('source','') %}
{% set repo_path = salt['pillar.get']('repo_path','') %}
{% set mount_dir = '/opt/seagate/cortx/updates' %}

{% if source == 'iso' %}
{% set iso_release = salt.cmd.run('basename ' ~repo_path~ '') %}
copy_iso:
  file.managed:
    - name: {{ repo_path }}
    - source: salt://{{ iso_release }}
    - keep_source: True

cortx_iso_mounted:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ repo_path }}
    - mkmnt: True
    - fstype: iso9660
    - persist: False

configure_prvsnr_repo:
  pkgrepo.managed:
    - name: provisioner
    - humanname: provisioner
    - baseurl: file://{{ mount_dir }}
    - gpgcheck: 0
    - enabled: 1
    - require:
      - cortx_iso_mounted

{% elif source== 'rpm '%}
configure_prvsnr_repo:
  pkgrepo.managed:
    - name: provisioner
    - humanname: provisioner
    - baseurl: {{ repo_path }}
    - gpgcheck: 0
    - enabled: 1
{% endif %}

{% if source == 'rpm' or source == 'iso' %}
install_prvsnr:
  pkg.installed:
    - pkgs:
      - cortx-prvsnr-cli 
      - cortx-prvsnr
    - require:
      - configure_prvsnr_repo
{% else %}
repo_installed:
  file.recurse:
    - name: {{ install_dir }}
    - source: salt://cortx-prvsnr
    - keep_source: True
    - clean: True  # ???
{% endif %}
