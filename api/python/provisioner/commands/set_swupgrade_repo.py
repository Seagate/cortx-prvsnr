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

from .set_swupdate_repo import SetSWUpdateRepo
from .. import inputs, values
from ..config import REPO_CANDIDATE_NAME, SW_UPGRADE_REPOS, YUM_REPO_TYPE

logger = logging.getLogger(__name__)


class SetSWUpgradeRepo(SetSWUpdateRepo):

    def dynamic_validation(self, params: inputs.SWUpgradeRepo, targets: str):  # noqa: C901, E501
        """

        Parameters
        ----------
        params: inputs.SWUpgradeRepo
            Input repository parameters
        targets: str
            Salt target to perform base mount and validation logic

        Returns
        -------

        """
        repo = params

        if repo.is_special():
            logger.info("Skipping update repo validation for special value: "
                        f"{repo.source}")
            return

        logger.info(f"Validating upgrade repo: release {repo.release}, "
                    f"source {repo.source}")

        candidate_repo = inputs.SWUpgradeRepo(REPO_CANDIDATE_NAME, repo.source)
        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        if self._does_repo_exist(f'sw_update_{candidate_repo.release}'):
            logger.warning(
                'other repo candidate was found, proceeding with force removal'
            )
            # TODO IMPROVE: it is not enough it may lead to locks when
            #  provisioner doesn't unmount `sw_update_candidate` repo
            # raise SWUpdateError(reason="Other repo candidate was found")

        try:
            logger.debug("Configuring upgrade candidate repo for validation")
            self._prepare_repo_for_apply(candidate_repo, enabled=False)

            super(SetSWUpdateRepo, self)._run(candidate_repo, targets)

            for repo_name, repo_info in SW_UPGRADE_REPOS.items():
                if repo_info[YUM_REPO_TYPE]:
                    # TODO: We have a single ISO which contains all repositories
                    # We can pass repo_name directly or give it from inputs.SWUpgrade
                    # instance. Another option is creation new instance for single
                    # repo
                    super(SetSWUpgradeRepo, self)._dynamic_validation(
                                                        repo, candidate_repo)
        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED
            logger.info("Post-validation cleanup")
            super(SetSWUpdateRepo, self)._run(candidate_repo, targets)

        return repo.metadata
