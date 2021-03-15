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

from test import helper as h


logger = logging.getLogger(__name__)


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.env_level('rpmbuild')
@pytest.mark.hosts(['srvnode1'])
def test_build_bundles(
    mhostsrvnode1,
    tmpdir_function,
    bundle_opts,
    bundle_script_path_f,
    orig_single_iso_on_host
):
    res = []

    build_script = bundle_script_path_f(mhostsrvnode1)

    b_types = [bundle_opts.type]
    upgrade_ver = bundle_opts.version

    if bundle_opts.type == 'all':
        upgrade_ver = upgrade_ver.split('.')
        upgrade_ver[-1] = str(int(upgrade_ver[-1]) + 1)
        upgrade_ver = '.'.join(upgrade_ver)
        b_types = h.BUNDLE_TYPES

    bundles = []
    for bt in b_types:
        bundles.append((
            tmpdir_function / bt, bt, (
                upgrade_ver if bundle_opts.type == 'upgrade'
                else bundle_opts.version
            )
        ))

    # XXX hard-coded
    for b_dir, b_type, b_version in bundles:
        add_opts = ''
        if b_type == 'deploy-bundle' and orig_single_iso_on_host:
            add_opts = f"--orig-iso {orig_single_iso_on_host}"

        mhostsrvnode1.check_output(
            f"{build_script} -o {b_dir} -t {b_type} -r {b_version}"
            f" --gen-iso {add_opts}"
        )
        res.append(mhostsrvnode1.copy_from_host(b_dir.with_suffix('.iso')))

    for iso_path in res:
        dest = bundle_opts.output
        if dest.is_dir():
            dest /= f"{iso_path.name}"
        dest.write_bytes(iso_path.read_bytes())
