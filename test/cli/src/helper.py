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


def run_script(
    mhost, script_path, *args, trace=False, stderr_to_stdout=True, env=None
):
    if env and type(env) is dict:
        env = ' '.join(["{}={}".format(k, v) for k, v in env.items()])

    return mhost.run(
        "{} bash {} {} {} {}"
        .format(
            env if env else '',
            '-x' if trace else '',
            script_path,
            ' '.join([*args]),
            '2>&1' if stderr_to_stdout else ''
        ), force_dump=trace
    )
