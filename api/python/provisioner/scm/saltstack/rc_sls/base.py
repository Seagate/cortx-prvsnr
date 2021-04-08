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

from typing import (
    ClassVar,
    Optional,
    Dict,
    Any,
    List,
    Tuple
)
from pathlib import Path
import importlib
import logging

from provisioner import config, values, errors
from provisioner.pillar import PillarKey, PillarResolverNew
from provisioner.values import _Singletone
from provisioner.vendor import attr
from provisioner.resources.base import (
    ResourceTransition,
    ResourceManagerT,
    ResourceManager
)
from provisioner.salt_api.base import SaltClientBase
# from provisioner.fileroot import ResourcePath

logger = logging.getLogger(__name__)

MODULE_PATH = Path(__file__)
MODULE_DIR = MODULE_PATH.resolve().parent

VENDOR_SLS_PREFIX = 'vendor'


@attr.s(auto_attribs=True)
class ResourceSLS(ResourceTransition):  # XXX ??? inheritance
    """Base class for Salt state formulas that implement transitions."""
    base_sls: ClassVar[Optional[str]] = None
    sls: ClassVar[Optional[str]] = None

    client: SaltClientBase
    pillar_inline: Dict = None

    _pillar: Optional[dict] = attr.ib(init=False, default=None)

    @property
    def resource_type(self) -> config.CortxResourceT:
        return self.state_t.resource_t.resource_t_id

    @property
    def resource_name(self) -> str:
        return self.resource_type.value

    @property
    def pillar(self):
        # XXX uses the pillar only
        if self._pillar is None:
            rc_key = PillarKey(self.resource_name)
            pillar = PillarResolverNew(client=self.client).get((rc_key,))
            self._pillar = {
                target: (
                    _pillar[rc_key]
                    if _pillar[rc_key] and _pillar[rc_key] is not values.MISSED
                    else {}
                ) for target, _pillar in pillar.items()
            }
        return self._pillar

    @property
    def is_vendored(self) -> bool:
        vendored = {
            pillar.get('vendored', False)
            for pillar in self.pillar.values()
        }
        if len(vendored) != 1:
            raise errors.ProvisionerRuntimeError(
                f"Mixed {self.resource_name} vendored setup"
                f" detected for targets '{self.targets}'"
            )
        return list(vendored)[0]

    def pillar_set(
        self, pillar: Dict, expand: bool = True,
        fpath=None
    ):
        return self.client.pillar_set({
            self.resource_name: pillar
        }, expand=expand, fpath=fpath, targets=self.targets)

    def set_vendored(self, vendored: bool):
        self.pillar_set(dict(vendored=vendored))

    # def r_path(self, path: Union[str, Path]):
    #    return ResourcePath(self.resource_t, path)

    # def fileroot_path(self, path: Union[str, Path]):
    #    return self.fileroot.path(self.r_path(path))

    def setup_roots(self):
        logger.info(
            f"Preparing '{self.resource_name}' roots for"
            f" '{self.state.name}' on targets: {self.targets}"
        )

    def run(self):
        self.setup_roots()

        res = []
        # XXX possibly a divergence with a design
        # some SLS may just shifts root without any states appliance
        if self.sls:
            fun_kwargs = {}
            if self.pillar_inline:
                fun_kwargs['pillar'] = self.pillar_inline

            slss = (
                self.sls if isinstance(self.sls, (List, Tuple)) else [self.sls]
            )

            if self.is_vendored:
                slss = [f'{VENDOR_SLS_PREFIX}.{sls}' for sls in slss]

            if self.base_sls:
                slss = [f'{self.base_sls}.{sls}' for sls in slss]

            for sls in slss:
                _res = self.client.state_apply(
                    sls, targets=self.targets, fun_kwargs=fun_kwargs
                )
                res.append(_res)

        return res


# arbitrary dir and recursive are not support for now
class TypesLoader:

    @staticmethod
    def load(
        base_t: Any, base_dir: Path = MODULE_DIR, recursive=False
    ):
        res = []

        if base_dir != MODULE_DIR or recursive:
            raise NotImplementedError()

        py_files = list(
            base_dir.glob('**/.*.py' if recursive else '*.py')
        )
        # if i.name not in (MODULE_PATH.name, '__init__.py')

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
