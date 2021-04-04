#!/usr/bin/env python3
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


import json
from pathlib import Path

CONFIG_PATH = '/etc/consul.d/config.json'
TELEMETRY_KEY = 'telemetry'
DISABLE_KEY = 'disable_compat_1.9'

config_path = Path(CONFIG_PATH)

config = json.loads(config_path.read_text())

if TELEMETRY_KEY not in config:
    config[TELEMETRY_KEY] = {}

telemetry = config[TELEMETRY_KEY]

telemetry[DISABLE_KEY] = (
    telemetry.get(DISABLE_KEY) or True
)

config_path.write_text(json.dumps(config, indent=4))
