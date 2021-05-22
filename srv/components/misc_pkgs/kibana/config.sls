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

Configure Kibana:
  file.managed:
    - name: /etc/kibana/kibana.yml
    - source: salt://components/misc_pkgs/kibana/files/kibana.yml.j2
    - template: jinja

Configure Kibana service:
  file.managed:
    - name: /etc/systemd/system/kibana.service
    - source: salt://components/misc_pkgs/kibana/files/kibana.service

Remove kibana security plugin:
  cmd.run:
    - name: "sudo /usr/share/kibana/bin/kibana-plugin remove opendistroSecurityKibana --allow-root"

Reload service units:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: Configure Kibana service
