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

include:
  - k8s.kube.stop

Reset kubeadm:
  cmd.run:
    - name: kubeadm reset
    - watch_in:
      - Stop kubelet service

# Remove Calico by creating the necessary custom resource:
#   cmd.run:
#     - name: kubectl delete -f https://docs.projectcalico.org/manifests/custom-resources.yaml

# Remove the Tigera Calico operator and custom resource definitions:
#   cmd.run:
#     - name: kubectl delete -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
#     - require:
#       - Remove Calico by creating the necessary custom resource
#     - watch_in:
#       - Stop kubelet service

Remove CNI config:
  file.absent:
    - name: /etc/cni/net.d

Remove kubeconfig file:
  file.absent:
    - name: ~/.kube/config

Remove kube packages:
  pkg.purged:
    - pkgs:
      - kubectl
      - kubelet
      - kubeadm

Setup package repo for kubectl:
  pkgrepo.absent:
    - name: kubernetes
