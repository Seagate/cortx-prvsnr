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
from ..config import REPO_CANDIDATE_NAME

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
            logger.info(
                "Skipping update repo validation for special value: "
                f"{repo.source}"
            )
            return

        logger.info(
            f"Validating update repo: release {repo.release}, "
            f"source {repo.source}"
        )

        candidate_repo = inputs.SWUpdateRepo(
            REPO_CANDIDATE_NAME, repo.source
        )
        try:
            logger.debug(
                "Configuring update candidate repo for validation"
            )
            self._prepare_repo_for_apply(candidate_repo, enabled=False)

            super()._run(candidate_repo, targets)

        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED
            logger.info("Post-validation cleanup")
            super()._run(candidate_repo, targets)

        return repo.metadata