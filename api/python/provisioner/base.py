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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

import os
from pathlib import Path

from . import config
from .values import _Singletone
from .utils import load_yaml
from copy import deepcopy

# TODO TEST
# TODO IMPROVE
#  - rename config.py
#  - then rename this file to config.py


class _Config(_Singletone):

    def __init__(self):
        self._path = None

        # TODO IMPROVE installation path should be likely in
        #      /etc/... or /opt/seagate/cortx/...
        for path in [
            config.PRVSNR_ROOT_DIR / config.PRVSNR_CONFIG_FILE,
            Path(__file__).parent / config.PRVSNR_CONFIG_FILE
        ]:
            if path.exists():
                self._path = path
                break

        self._logging_default = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'full': {
                    'format': (
                        '%(asctime)s - %(thread)d - %(name)s - %(levelname)s - '  # noqa: E501
                        '[%(filename)s:%(lineno)d]: %(message)s'  # noqa: E501
                    )
                }
            },
            'handlers': {
                config.LOG_NULL_HANDLER: {
                    'class': 'logging.NullHandler',
                },
                config.LOG_CONSOLE_HANDLER: {
                    'class': 'logging.StreamHandler',
                    'formatter': 'full',
                    'level': 'DEBUG',
                    'stream': 'ext://sys.stderr'
                }
            },
            'root': {
                'handlers': [
                    config.LOG_NULL_HANDLER,
                    config.LOG_CONSOLE_HANDLER
                ],
                'level': 0
            },
        }

        self._value = (
            load_yaml(self._path) if self._path else {
                'logging': self._logging_default
            }
        )

        # TODO DOC
        self._env = {}
        for env, default_v in (
            ('PRVSNR_OUTPUT', 'PRVSNR_CLI_OUTPUT_DEFAULT'),
        ):
            self._env[env] = os.getenv(env, getattr(config, default_v))

    @property
    def path(self):
        return self._path

    @property
    def value(self):
        return deepcopy(self._value)

    @property
    def logging_default(self):
        return deepcopy(self._logging_default)

    @property
    def env(self):
        return deepcopy(self._env)

    def __getattr__(self, name):
        try:
            return self.value[name]
        except KeyError:
            raise AttributeError


prvsnr_config = _Config()
