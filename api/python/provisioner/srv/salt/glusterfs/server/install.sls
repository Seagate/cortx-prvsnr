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
chrony_installed:
  pkg.installed:
    - name: chrony


chronyd_running:
  service.running:
    - name: chronyd.service
    - require:
        - chrony_installed

{% if salt['pillar.get']('glusterfs:in_docker', False) %}

glusterfs_server_dirs_exist:
  file.directory:
    - names:
      - /etc/glusterfs
      - /var/lib/glusterd
      - /var/log/glusterfs
      - /srv/glusterfs
    - makedirs: True
    - user: root
    - group: root

glusterfs_server_docker_running:
  docker_container.running:
    - name: glusterd
    - image: gluster/gluster-centos
    - binds:
      - /etc/glusterfs:/etc/glusterfs:z
      - /var/lib/glusterd:/var/lib/glusterd:z
      - /var/log/glusterfs:/var/log/glusterfs:z
      - /srv/glusterfs:/srv/glusterfs:z
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    - privileged: True
    - network_mode: host
    - detach: True

gluster_tool_is_available:
  file.managed:
    - name: /usr/bin/gluster
    - contents: |
        #!/bin/bash
        docker exec -i glusterd bash -c "gluster $*"
    - mode: 755

{% else %}

include:
  - ..install

glusterfs_server_installed:
  pkg.installed:
    - pkgs:
      - glusterfs-server
    - require:
      - glusterfs_repo_is_installed

glusterfs_daemon_running:
  service.running:
    - name: glusterd.service
    - require:
        - glusterfs_server_installed

{% endif %}
