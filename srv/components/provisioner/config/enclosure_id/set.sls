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

{% set enclosure = "enclosure-" + ((grains['id']).split('-'))[1] %}

{% if "physical" in grains['virtual'] %}
  # Hardware
  {% set ctrl_utility = "/opt/seagate/cortx/provisioner/srv/components/controller/files/scripts/controller-cli.sh" %} 
  {% set host = pillar['storage'][enclosure ]['controller']['primary']['ip'] %}
  {% set user = pillar['storage'][enclosure]['controller']['user'] %}
  {% set secret = salt['lyveutil.decrypt']('storage', pillar['storage'][enclosure]['controller']['secret']) %}
  {% set opt = "--show-license" %}
  {% set logs = "/var/log/seagate/provisioner/controller-cli.log" %}

Create script to generate enclosure id:
  file.managed:
      - name: /tmp/get_enclosure_id.sh
      - create: True
      - makedirs: True
      - replace: True
      - user: root
      - group: root
      - mode: 755
      - contents: |
          #!/bin/bash
          echo "Running controller-cli utility to get enclosure serial"
          sh {{ ctrl_utility }} host -h {{ host }} -u {{ user }} -p '{{ secret }}' {{ opt }} | grep -A2 Serial | tail -1 > /etc/enclosure_id
          if [[ ! -s /etc/enclosure_id ]]; then
              echo "ERROR: Could not generate the enclosure id from controller cli utility, please check the {{ logs }} for more details"
              exit 1
          elif [[ `cat /etc/enclosure_id | wc -w` -ne 1 ]]; then
              echo "ERROR: The contents of /etc/enclosure_id looks incorrect, failing"
              exit 1
          else
              echo "Enclosure id generated successfully and is kept at /etc/enclosure_id"
              exit 0
          fi

#Run the script created above
Get enclosure_id for {{ grains['id'] }}: 
  cmd.run:
    - name: bash /tmp/get_enclosure_id.sh
    - require:
      - Create script to generate enclosure id

{% else %}

# VM
  {% if salt['file.file_exists']('/etc/machine-id') %}
    {% set machine_id = salt['cmd.shell']("cat /etc/machine-id") %}
Get enclosure_id for {{ grains['id'] }}:
  cmd.run:
    - name: echo "enc_{{ machine_id }}" > /etc/enclosure-id
  {% else %}
Get enclosure_id for {{ grains['id'] }}:
  test.show_notification:
    - text: "Can't not set the enclosure id on VM as there is not machine id set on {{ grains['id'] }}"
  {% endif %}
{% endif %}

Replace enclosure id in grains:
    cmd.run:
      - name: 'enclosure_id=`cat /etc/enclosure-id`; sed -ie "s/enclosure_id:*.*/enclosure_id: ${enclosure_id}/" /etc/salt/grains'
      - require:
        - Get enclosure_id for {{ grains['id'] }}

Sync grains data after refresh enclosure_id:
  module.run:
    - saltutil.refresh_grains: []
    - require:
      - Replace enclosure id in grains

Update enclosure_ids in pillar:
  cmd.run:
    - name: provisioner pillar_set storage/{{ enclosure }}/enclosure_id \"{{ grains['enclosure_id'] }}\"
