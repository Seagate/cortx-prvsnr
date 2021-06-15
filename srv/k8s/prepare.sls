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


Create containerd module config file for k8s:
  file.managed:
    - name: /etc/modules-load.d/containerd.conf
    - contents:
        - overlay
        - br_netfilter
    - user: root
    - group: root
    - mode: 644

Execute modprobe overlay:
  cmd.run:
    - name: modprobe overlay

Execute modprobe br_netfilter:
  cmd.run:
    - name: modprobe br_netfilter

Create file to persist systemctl params across reboots:
  file.managed:
    - name: /etc/sysctl.d/99-kubernetes-cri.conf
    - contents:
        - net.bridge.bridge-nf-call-iptables  = 1
        - net.ipv4.ip_forward                 = 1
        - net.bridge.bridge-nf-call-ip6tables = 1
    - user: root
    - group: root
    - mode: 644

Apply sysctl params without reboot:
  cmd.run:
    - name: sysctl --system

Cleanup old docker versions:
  pkg.purged:
    - pkgs:
      - docker
      - docker-client
      - docker-client-latest
      - docker-common
      - docker-latest
      - docker-latest-logrotate
      - docker-logrotate
      - docker-engine
