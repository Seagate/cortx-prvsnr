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

Install prereq packages for NFS:
  pkg.installed:
    - pkgs:
      - jemalloc
      - krb5-devel
      - libini_config-devel
      - krb5-server
      - krb5-libs
      - nfs-utils
      - rpcbind
      - libblkid
      - libevhtp

{% for path in [
  "/usr/lib64/libcap.so",
  "/usr/lib64/libjemalloc.so",
  "/usr/lib64/libnfsidmap.so",
  "/usr/lib64/libblkid.so"
] %}
{{ path }}.1:
  file.symlink:
    - target: {{ path }}
    - force: True
    - makedirs: True
{% endfor %}

Install NFS Ganesha:
  pkg.installed:
    - name: nfs-ganesha

Install NFS packages:
  pkg.installed:
    - pkgs:
      - cortx-dsal
      - cortx-dsal-devel
      - cortx-fs
      - cortx-fs-devel
      - cortx-fs-ganesha
      - cortx-fs-ganesha-test
      - cortx-nsal
      - cortx-nsal-devel
      - cortx-utils
      - cortx-utils-devel
    - disableexcludes: main
