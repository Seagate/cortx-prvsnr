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

{% set fileroot_prefix = salt['pillar.get']('inline:fileroot_prefix', '') %}
{% set install_dir = salt['pillar.get']('provisioner:install_dir', '/opt/seagate/cortx/provisioner') %}


# TODO FIXME salt always extracts despite of source_hash & source_hash_update
# TODO archive.extracted supports also https:// and local to a minion sources
provisioner_archive_extracted:
  archive.extracted:
    - name: {{ install_dir.rstrip('/') }}
    - source: salt://{{ fileroot_prefix }}provisioner/core/files/repo.tgz
    - source_hash: {{ salt['pillar.get']('provisioner:repo:tgz:hash') }}
    - source_hash_update: True
    - keep_source: True
    - clean: False
    - overwrite: True
    - enforce_toplevel: False
    - trim_output: True


cluster_sls_prepared:
  file.managed:
    - name: {{ install_dir }}/pillar/components/cluster.sls
    - source: {{ install_dir }}/pillar/samples/dualnode.cluster.sls
    - keep_source: True
