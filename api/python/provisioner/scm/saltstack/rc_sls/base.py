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

from typing import ClassVar, Optional, Dict, Union, Any
from pathlib import Path
import importlib
import logging

from provisioner.values import _Singletone
from provisioner.vendor import attr
from provisioner.resources.base import (
    ResourceTransition,
    ResourceManagerT,
    ResourceManager
)
from provisioner.salt_api.base import SaltClientBase
from provisioner.fileroot import ResourcePath
from provisioner import config

logger = logging.getLogger(__name__)

MODULE_PATH = Path(__file__)
MODULE_DIR = MODULE_PATH.resolve().parent


@attr.s(auto_attribs=True)
class ResourceSLS(ResourceTransition):  # XXX ??? inheritance
    """Base class for Salt state formulas that implement transitions."""
    sls: ClassVar[Optional[str]] = None

    client: SaltClientBase
    pillar_inline: Dict = None

    def r_path(self, path: Union[str, Path]):
        return ResourcePath(self.resource_t, path)

    def fileroot_path(self, path: Union[str, Path]):
        return self.fileroot.path(self.r_path(path))

    def setup_roots(self, targets):
        pass

    def run(self, targets: Any = config.ALL_TARGETS):
        self.setup_roots(targets)

        # XXX possibly a divergence with a design
        # some SLS may just shifts root without any states appliance
        if self.sls:
            fun_kwargs = {}
            if self.pillar_inline:
                fun_kwargs['pillar'] = self.pillar_inline

            self.client.state_apply(
                self.sls, targets=targets, fun_kwargs=fun_kwargs
            )


# arbitrary dir and recursive are not support for now
class TypesLoader:

    @staticmethod
    def load(
        base_t: Any, base_dir: Path = MODULE_DIR, recursive=False
    ):
        res = []

        if base_dir != MODULE_DIR or recursive:
            raise NotImplementedError()

        py_files = [
            i for i in base_dir.glob('**/.*.py' if recursive else '*.py')
            # if i.name not in (MODULE_PATH.name, '__init__.py')
        ]

        modules = [
            importlib.import_module(f'{__package__}.{f.stem}')
            for f in py_files
        ]

        for mod in modules:
            for _attr_name in dir(mod):
                _attr = getattr(mod, _attr_name)

                try:
                    # we either fails with TypeError (not a class) or
                    # we raise the error explicitly if False (not a subclass)
                    if not issubclass(_attr, base_t):
                        raise TypeError
                except TypeError:
                    pass
                else:
                    res.append(_attr)

        return res


@attr.s(auto_attribs=True)
class SLSResourceManager(ResourceManager, _Singletone):

    engine_t = ResourceManagerT.SALTSTACK

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

        sls_types = TypesLoader.load(ResourceSLS)

        self.transitions.update(
            {sls_t.state_t: sls_t for sls_t in sls_types if sls_t.state_t}
        )
