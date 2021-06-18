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


from ..command import Command
from cortx_setup.config import CERT_PATH
from cortx_setup.validate import path, CortxSetupError
from provisioner.utils import run_subprocess_cmd
from datetime import datetime


class SecurityConfig(Command):
    _args = {
        'certificate': {
            'type': path,
            'optional': True,
            'help': 'Install security certificate'
        }
    }

    def run(self, certificate=None):
        self.logger.debug(f"Ceritifact path: {certificate}")
        CERT_PATH.mkdir(parents=True, exist_ok=True)
        if certificate:
            try:
                end_date = None
                # pyOpenSSL will not be available by default
                # on centos JIRA: EOS-21290
                res = run_subprocess_cmd(
                    f"openssl x509 -enddate -noout -in {certificate}"
                )
                if not res.returncode:
                    res = res.stdout
                    end_date = res.split('=')[1]
                    ed = datetime.strptime(
                             end_date.strip(), '%b %d %H:%M:%S %Y %Z')
                    current_d = datetime.now()
                    if current_d > ed:
                        raise CortxSetupError(
                            f"Certificate {certificate} is expired "
                            f"End date: {ed}"
                        )
            except Exception as exc:
                self.logger.error(
                    f"Invalida ceritificate file {certificate}\n"
                    f"Error: {exc}")
                raise
            self.logger.debug(f"Copy certificate to {str(CERT_PATH)}")
            run_subprocess_cmd(f"cp -rf {certificate} {str(CERT_PATH)}")
        self.logger.debug("Done")
