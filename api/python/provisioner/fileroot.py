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
from typing import Any, Union, Optional
from pathlib import Path

from .vendor import attr
from .paths import FileRootPath, USER_SHARED_FILEROOT
from .salt_api.base import SaltClientBase
from .salt_api.runner import SaltRunnerClient
from . import utils

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class FileRoot:
    _root: FileRootPath = USER_SHARED_FILEROOT
    refresh_on_update: bool = True
    local_runner_client: Optional[SaltClientBase] = attr.Factory(
        SaltRunnerClient
    )

    def refresh(self):
        # TODO DOC
        # ensure it would be visible for salt-master / salt-minions
        # TODO makes sense to move to client, so ssh and runner clients
        #      may do that in a different way
        self.local_runner_client.run(
            'fileserver.clear_file_list_cache',
            fun_kwargs=dict(backend='roots')
        )

    @property
    def root(self):
        return self._root

    def path(self, r_path: Union[str, Path]):
        return self.root.path(r_path)

    def exists(self, r_path: Union[str, Path]):
        return self.path(r_path).exists()

    def read(self, r_path: Union[str, Path], text: bool = True):
        path = self.path(r_path)
        return path.read_text() if text else path.read_bytes()

    def read_yaml(self, r_path: Union[str, Path]):
        return utils.load_yaml(self.path(r_path))

    # TODO make idempotent
    # TODO option to create parent dirs if not exists
    def write(
        self,
        r_path: Union[str, Path],
        data: Any,
        text: bool = True
    ):
        path = self.path(r_path)

        if text:
            path.write_text(data)
        else:
            path.write_bytes(data)

        if self.refresh_on_update:
            self.refresh()

    # TODO make idempotent
    def write_yaml(self, r_path: Union[str, Path], data: Any):
        return self.write(r_path, utils.dump_yaml_str(data), text=True)

    # FIXME mostly duplicates salt:copy_to_file_roots
    def copy(
        self, source: Union[str, Path], r_dest: Union[str, Path],
    ):
        source = Path(str(source))
        dest = self.path(r_dest)

        if not source.exists():
            raise ValueError('{} not found'.format(source))

        if source.is_dir():
            # TODO
            #  - file.recurse expects only dirs from salt-master file roots
            #    (salt://), need to find another alternative to respect
            #    indempotence
            # StateFunExecuter.execute(
            #     'file.recurse',
            #     fun_kwargs=dict(
            #       source=str(params.source),
            #       name=str(dest)
            #     )
            # )
            self.local_runner_client.cmd_run(
                "mkdir -p {0} && rm -rf {2} && cp -R {1} {2}"
                .format(dest.parent, source, dest)
            )
        else:
            self.local_runner_client.state_single(
                'file.managed',
                fun_kwargs=dict(
                    source=str(source),
                    name=str(dest),
                    makedirs=True
                )
            )

        if self.refresh_on_update:
            self.refresh()

        return dest
