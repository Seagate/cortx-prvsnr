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

# Check: Node is primary and not a VM (No STONITH for VMs)
{%  if 'primary' in grains['roles']
    and "physical" in grains['virtual']
    and pillar['cluster'][grains['id']]['bmc']['ip']
%}
Remove stonith id stonith-c1 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c1
    - onlyif: pcs stonith show stonith-c1

Remove stonith id stonith-c2 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c2
    - onlyif: pcs stonith show stonith-c2

# Ref: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_and_managing_high_availability_clusters/assembly_configuring-fencing-configuring-and-managing-high-availability-clusters
Prepare for stonith on node-1:
  cmd.run:
    - name: pcs stonith create stonith-c1 fence_ipmilan ipaddr={{ pillar['cluster']['srvnode-1']['bmc']['ip'] }} login={{ pillar['cluster']['srvnode-1']['bmc']['user'] }} passwd={{ salt['lyveutils.decrypt']('cluster', pillar['cluster']['srvnode-1']['bmc']['secret']) }} delay=20 pcmk_host_list=srvnode-1 pcmk_host_check=static-list lanplus=true auth=PASSWORD power_timeout=40 verbose=true op monitor interval=10s meta failure-timeout=15s
    - unless: pcs stonith show stonith-c1

Prepare for stonith on node-2:
  cmd.run:
    - name: pcs stonith create stonith-c2 fence_ipmilan ipaddr={{ pillar['cluster']['srvnode-2']['bmc']['ip'] }} login={{ pillar['cluster']['srvnode-2']['bmc']['user'] }} passwd={{ salt['lyveutils.decrypt']('cluster', pillar['cluster']['srvnode-2']['bmc']['secret']) }} pcmk_host_list=srvnode-2 pcmk_host_check=static-list lanplus=true auth=PASSWORD power_timeout=40 verbose=true op monitor interval=10s meta failure-timeout=15s
    - unless: pcs stonith show stonith-c2

Apply stonith for node-1:
  cmd.run:
    - name: pcs constraint location stonith-c1 avoids srvnode-1=INFINITY

Apply stonith for node-2:
  cmd.run:
    - name: pcs constraint location stonith-c2 avoids srvnode-2=INFINITY

Set Stonith to poweroff:
  cmd.run:
    - name: pcs property set stonith-action=off
{% else %}

No STONITH application:
  test.show_notification:
    - text: "STONITH configuration applies only to primary node on a physical HW. There's no execution on secondary node or VM."

{% endif %}
