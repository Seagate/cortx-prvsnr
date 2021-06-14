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


Insert Cgroups info:
  file.line:
    - name: /usr/lib/systemd/system/kubelet.service.d/10-kubeadm.conf
    - content: |
        Environment=”cgroup-driver=systemd/cgroup-driver=cgroupfs”
    - mode: ensure
    - before: EnvironmentFile=-/var/lib/kubelet/kubeadm-flags.env


include:
  - k8s.kube.stop
  - k8s.kube.start

{% if 'srvnode-1' in grains['id'] %}
Reset k8s cluster with kubeadm:
  cmd.run:
    - name: kubeadm reset --force
    - requires:
      - Stop kubelet service
    - watch_in:
      - Start kubelet service

Initialize kubeadm:
  cmd.run:
    - name: kubeadm init --pod-network-cidr=192.168.0.0/16

Copy kube config file:
  file.copy:
    - name: ~/.kube/config
    - source: /etc/kubernetes/admin.conf
    - makedirs: True
    - force: True
    - user: {{ grains['username'] }}
    - group: {{ grains['groupname'] }}

Allow pods scheduling on all nodes:
  cmd.run:
    - name: kubectl taint nodes --all node-role.kubernetes.io/master-
{% endif %}
