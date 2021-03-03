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
chrony_installed:
  pkg.installed:
    - name: chrony


{% if salt['grains.get']('virtual') != 'container' %}

chronyd_running:
  service.running:
    - name: chronyd.service
    - require:
        - chrony_installed

{% endif %}

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
  - ..prepare

glusterfs_server_installed:
  pkg.installed:
    - pkgs:
      - glusterfs-server
    {% if salt['pillar.get']('glusterfs:add_repo', False) %}
    - require:
      - glusterfs_repo_is_installed
    {% endif %}

glusterfs_daemon_running:
  service.running:
    - name: glusterd.service
    - enable: True
    - require:
        - glusterfs_server_installed

{% endif %}
