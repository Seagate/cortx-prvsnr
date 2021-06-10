#!/bin/bash
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

set -eu

! read -r -d '' _script << EOF
from pathlib import Path
from provisioner.utils import repo_tgz, calc_hash
from provisioner.config import PROJECT_PATH, HashType

dest = Path(f"{PROJECT_PATH}/.build/repo.tgz")
dest.parent.mkdir(parents=True, exist_ok=True)

if dest.exists():
    dest.unlink()

repo_tgz(
    dest,
    include_dirs=[
        'cli',
        'files',
        'pillar',
        'srv',
        'api'
    ]
)

EOF

python -c "$_script"
