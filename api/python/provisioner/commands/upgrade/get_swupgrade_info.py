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
import logging
from typing import Type

from packaging import version
from provisioner import inputs
from provisioner.config import (CORTX_ISO_DIR, REPO_CANDIDATE_NAME,
                                SWUpgradeInfoFields)
from provisioner.pillar import PillarResolver, PillarKey

from provisioner.salt import local_minion_id, cmd_run
from provisioner.commands import CommandParserFillerMixin
from provisioner.vendor import attr


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class GetSWUpgradeInfoArgs:
    release: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "SW upgrade repository release version"
            }
        },
        default=None
    )


class GetSWUpgradeInfo(CommandParserFillerMixin):
    """
    Base class that provides API for getting SW upgrade repository information.

    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = GetSWUpgradeInfoArgs

    @staticmethod
    def _get_package_version(release: str) -> dict:
        """
        Function returns information about CORTX packages and their versions.

        Parameters
        ----------
        release : str
            SW upgrade repository version

        Returns
        -------
        dict
            return dictionary with CORTX packages and their versions

        """
        repo = f"sw_upgrade_{CORTX_ISO_DIR}_{release}"

        cmd = (f"yum repo-pkgs {repo} list 2>/dev/null | "
               f"grep '{repo}' | awk '{{print $1\" \"$2}}'")

        res = cmd_run(cmd, targets=local_minion_id(),
                      fun_kwargs=dict(python_shell=True))

        packages = res[local_minion_id()].strip().split('\n')

        if packages:
            logger.debug(f"List of packages in repository '{repo}':"
                         f" {packages}")
        else:
            logger.debug(f"There are no packages in repository '{repo}'")

        res = dict()
        # NOTE: Format is following
        # ```
        #  {
        #      'cortx-motr': {
        #             'version': '2.0.0-277',
        #          },
        #  }
        # ```
        #
        # TODO: EOS-20507: Along the with 'version', field we need to add
        #  'constraint version' field to provide necessary information about
        #  compatibility with old versions
        for entry in packages:
            pkg, ver = entry.split(" ")
            res[pkg] = {SWUpgradeInfoFields.VERSION.value: ver}

        return res

    def run(self, release: str = None) -> dict:
        """
        Main function for Get SW Upgrade Repo command. Command returns
        information about CORTX packages and their versions.

        Parameters
        ----------
        release: str
            SW upgrade repository release version

        Returns
        -------
        dict:
            return dictionary with CORTX packages and their versions

        """
        local_minion = local_minion_id()

        if release is None:
            # NOTE: take the latest release from SW upgrade repositories

            # TODO: make get pillar API public and available for others to
            #  avoid code duplication
            pillars = PillarResolver(local_minion).get(
                [PillarKey('release/upgrade/repos')],
                fail_on_undefined=True
            )

            upgrade_releases = list(pillars[local_minion][
                PillarKey('release/upgrade/repos')].keys())

            upgrade_releases.remove(REPO_CANDIDATE_NAME)

            # NOTE: Assumption: we expect that SW Upgrade release version
            # is formatted according to PEP-440
            release = max(upgrade_releases, key=version.parse)

        return self._get_package_version(release)
