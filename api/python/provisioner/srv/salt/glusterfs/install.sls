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

# TODO detect centos instead
{% if "RedHat" not in grains['os'] %}

glusterfs_repo_is_installed:
  pkg.installed:
    - pkgs:
      - centos-release-gluster7

{% else  %}

# FIXME need to use gluster from official  RedHat repos
# centos-release-gluster7 not available for redhat hence adding repo manually
glusterfs_repo_is_installed:
  pkgrepo.managed:
    - name: glusterfs
    - humanname: glusterfs-7
    - baseurl: http://mirror.centos.org/centos/7/storage/x86_64/gluster-7/
    - gpgcheck: 0
    - enabled: 1

{% endif %}
