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

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules


import asyncio
import json
import logging

from pathlib import Path


logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


class CortxUnsupportedFeatures(object):
    # Unsupported features library
    _ufl = None
    _us_features_schema = None


    def __init__(self):
        from cortx.utils.product_features import unsupported_features
        self._ufl = unsupported_features
        self._us_features_schema = Path("/opt/seagate/cortx/csm/schema/unsupported_features.json")


    def _update_unsupported_schema_dict(
        self,
        unsupported_schema_dict,
        setup_type,
        unsupported_feature_list
    ):
        logger.debug(f"Unsupported schema to register: {json.dumps(unsupported_schema_dict)}")
        for entry in unsupported_schema_dict["setup_types"]:
            if entry["name"] == setup_type:
                entry[
                    "unsupported_features"
                ].extend(
                    unsupported_feature_list
                )
        return unsupported_schema_dict


    def _update_unsupported_schema(
        self,
        unsupported_feature_list,
        setup_types
    ):
        _us_features_dict = json.loads(
            self._us_features_schema.read_text()
        )

        logger.debug(
            "The existing unsupported features schema: "
            f"{_us_features_dict}"
        )

        if setup_types and unsupported_feature_list:
            # Here we iterate the setup types from input
            # over the setup types from the schema file.
            # Any entries from input not in schema are unsupported
            # and not considered.
            for setup_type in setup_types:
                _us_features_dict.update(
                    self._update_unsupported_schema_dict(
                        unsupported_schema_dict = _us_features_dict,
                        setup_type = setup_type,
                        unsupported_feature_list = unsupported_feature_list
                    )
                )
        else:
            logger.warning(
                f"Unable to update unsupported features schema."
            )
            logger.debug(
                f"Either setup_types parameter is empty: {setup_types} "
                " or "
                f"unsupported features list is empty: {unsupported_feature_list}"
            )

        logger.debug(
            "The updated unsupported features schema: "
            f"{_us_features_dict}"
        )

        self._us_features_schema.write_text(
            json.dumps(
                _us_features_dict,
                indent = 4
            )
        )


    async def set_unsupported_feature_info(
        self,
        component,
        unsupported_feature_list
    ):
        if component and unsupported_feature_list:
            _uf_db_instance = self._ufl.UnsupportedFeaturesDB()
            await _uf_db_instance.store_unsupported_features(
                component_name=component,
                features=unsupported_feature_list
            )


    async def get_unsupported_features(self, component):
        ret_val = None
        if component:
            _uf_db_instance = self._ufl.UnsupportedFeaturesDB()
            ret_val = await _uf_db_instance.get_unsupported_features(
                component_name = component
            )

        return ret_val


def register(
        component,
        unsupported_feature_list,
        setup_types
    ):
    """ Define list of Cortx unsupported features.

        Check with CSM team to get the list of usable feature IDs.
        By default we disable FW upgrade on virtual environments.
    """
    # CortxUnsupportedFeatures class init
    cuf = CortxUnsupportedFeatures()

    logger.debug(f"Unsupported schema list: {unsupported_feature_list}")
    logger.debug(
        "Setup types to register"
        f"for unsupported schema list: {setup_types}"
    )
    cuf._update_unsupported_schema(
        unsupported_feature_list,
        setup_types
    )

    loop = asyncio.get_event_loop()
    if component and unsupported_feature_list:
        loop.run_until_complete(
            cuf.set_unsupported_feature_info(
                component,
                unsupported_feature_list
            )
        )

        # Verify the unsupported feature is set
        feature_list = loop.run_until_complete(
            cuf.get_unsupported_features(component)
        )
        logger.debug(
            "The registered feature list: "
            f"{feature_list}"
        )

        for entry in feature_list:
            if entry["feature_name"] not in unsupported_feature_list:
                logger.error(
                    "Unsupported feature list: "
                    f"{feature_list} doesn't include the requested "
                    f"features to be supported: {unsupported_feature_list}"
                )
                return False
    else:
        logger.warning(
            f"Unable to set unsupported features."
        )
        logger.debug(
            f"Either component parameter is empty: {component} "
            " or "
            f"unsupported features list is empty: {unsupported_feature_list}"
        )
        return False

    return True
