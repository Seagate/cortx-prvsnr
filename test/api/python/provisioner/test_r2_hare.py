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
from provisioner.hare import r2_check_cluster_health_status
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_cluster_health_status():
    with patch("provisioner.hare.CortxClusterManager", MagicMock) as mh:
        mh.cluster_controller = MagicMock()
        mh.cluster_controller.status.side_effect = Exception("Some Exception")

        assert r2_check_cluster_health_status() is False

        mh.cluster_controller = MagicMock()
        mh.cluster_controller.status.return_value = dict()

        assert r2_check_cluster_health_status() is False

        mh.cluster_controller = MagicMock()
        mh.cluster_controller.status.return_value = dict(res=True)

        assert r2_check_cluster_health_status() is True
