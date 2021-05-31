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


from provisioner import inputs, utils

from provisioner.commands.validator import AuthenticityValidator
from provisioner.config import ISOValidationFields, CheckVerdict

from provisioner.errors import ValidationError

from provisioner.commands import CommandParserFillerMixin
from provisioner.salt import cmd_run, local_minion_id
from provisioner.vendor import attr


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class CheckISOAuthenticityArgs:
    iso_path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Path to the SW upgrade single ISO bundle"
            }
        },
        converter=utils.converter_path_resolved,
        default=None
    )
    sig_file: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Path to the file with ISO signature"
            }
        },
        validator=attr.validators.optional(utils.validator_path_exists),
        converter=utils.converter_path_resolved,
        default=None
    )
    gpg_pub_key: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "(Optional) Path to the custom GPG public key"
            }
        },
        validator=attr.validators.optional(utils.validator_path_exists),
        converter=utils.converter_path_resolved,
        default=None
    )
    import_pub_key: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': ("(Optional) Specifies whether to import a given GPG "
                         "public key or not")
            }
        },
        default=False
    )


@attr.s(auto_attribs=True)
class CheckISOAuthenticity(CommandParserFillerMixin):
    """
    Base class that provides API for getting SW upgrade repository information.

    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = CheckISOAuthenticityArgs

    @staticmethod
    def _import_gpg_public_key(gpg_pub_key: str):
        """
        Import GPG public key

        Returns
        -------

        """
        cmd = f'gpg --import {gpg_pub_key}'

        cmd_run(cmd, targets=local_minion_id(),
                fun_kwargs=dict(python_shell=True))

    def run(self, iso_path: str, sig_file: str, gpg_pub_key: str = None,
            import_pub_key: bool = False):
        """
        Validate SW Upgrade single ISO authenticity using GPG tool.

        Parameters
        ----------
        iso_path: str
            Path to the SW upgrade single ISO bundle
        sig_file: str
            Path to the file with ISO signature
        gpg_pub_key: str
            (Optional) Path to the custom GPG public key
        import_pub_key: bool
            (Optional) Specifies whether to import a given GPG public key
            or not

        Returns
        -------

        """
        if import_pub_key and gpg_pub_key is not None:
            self._import_gpg_public_key(gpg_pub_key)
            gpg_pub_key = None  # NOTE: GPG public key is already imported

        auth_validator = AuthenticityValidator(signature=sig_file,
                                               gpg_public_key=gpg_pub_key)

        try:
            output = auth_validator.validate(iso_path)
        except ValidationError as e:
            logger.warning(f"ISO authenticity check is failed: '{e}'")
            return {
                ISOValidationFields.STATUS.value: CheckVerdict.FAIL.value,
                ISOValidationFields.MSG.value: f'{e}'
            }
        else:
            logger.info("ISO authenticity check succeeded")
            return {
                ISOValidationFields.STATUS.value: CheckVerdict.PASSED.value,
                ISOValidationFields.MSG.value: f'{output}'
            }
