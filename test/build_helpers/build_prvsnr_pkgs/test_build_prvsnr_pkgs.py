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

import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.mark.isolated
def test_build_bundles(
    request, rpm_build, tmpdir_function, bundle_opts,
):
    prvsnr_pkg = rpm_build(
        request, tmpdir_function, rpm_type='core',
        version=bundle_opts.version,
        release_number=str(bundle_opts.pkg_version)
    )
    prvsnr_api_pkg = rpm_build(
        request, tmpdir_function, rpm_type='api',
        pkg_version=str(bundle_opts.pkg_version)
    )

    for pkg in (prvsnr_pkg, prvsnr_api_pkg):
        dest = bundle_opts.output / pkg.name
        dest.write_bytes(pkg.read_bytes())
