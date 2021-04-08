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

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional, Type, Dict
from pathlib import Path
from enum import Enum
import logging
# import importlib

# import itertools

from ..vendor import attr
from ..config import ALL_TARGETS, CortxResourceT
# from ..values import _Singletone

logger = logging.getLogger(__name__)

MODULE_PATH = Path(__file__)
MODULE_DIR = MODULE_PATH.resolve().parent


class ResourceManagerT(Enum):
    """SCM types"""
    SALTSTACK = 'saltstack'


# class SetupOST(Enum):
#     """Target platform types"""
#     CENTOS_7 = 'centos7'
#     CENTOS_8 = 'centos8'


# @attr.s(auto_attribs=True)
# class SetupManager:
#     engine: SetupEngineType = SetupEngineType.SALTSTACK
#     os: SetupEngineType = SetupOSType.CENTOS_8
#
#     def __attrs_post_init__(self):
#         self.name = self._attr.name
#         self._register = COMPONENTS_REGISTER


class ResourceParams:
    """Base class for resource parameters."""


@attr.s(auto_attribs=True)
class ResourceBase:
    """Base class for resources.

    ...

    Attributes
    ----------
    name : string
        Name of the resource.

    """
    resource_t_id: ClassVar[Optional[CortxResourceT]] = None
    params_t: ClassVar[Optional[Type[ResourceParams]]] = None


@attr.s(auto_attribs=True)
class ResourceState:
    """Base class for resource state."""
    name: ClassVar[Optional[str]] = None
    resource_t: ClassVar[Optional[Type[ResourceBase]]] = None


@attr.s(auto_attribs=True)
class ResourceTransition(ABC):
    """Base class for resource state transitions."""
    state_t: ClassVar[Optional[Type[ResourceState]]] = None

    state: ResourceState = attr.ib(
        validator=attr.validators.instance_of(ResourceState)
    )
    targets: str = ALL_TARGETS

    # XXX need abstraction for targets:
    #     - different SCM might use different aliases for all targets,
    #       different bulk targeting (lists, globs, regex ...)
    @abstractmethod
    def run(self):
        """Move a resource to a state"""


@attr.s(auto_attribs=True)
class ResourceManager:
    """Base class for resource state transitions."""
    engine_t: ClassVar[Optional[Type[ResourceManagerT]]] = None

    transitions: Dict[
        Type[ResourceState], Type[ResourceTransition]
    ] = attr.Factory(dict)

    def __attrs_post_init__(self):
        pass

    def run(
        self,
        state: ResourceState,
        *args,
        targets: Any = ALL_TARGETS,
        trans_args=None, trans_kwargs=None,
        **kwargs
    ):
        """Apply state on specified targets."""

        try:
            transition_t = self.transitions[type(state)]  # pylint: disable=unsubscriptable-object
        except KeyError:
            raise TypeError(f'unsupported state type {type(state)}')

        if trans_args is None:
            trans_args = []

        if trans_kwargs is None:
            trans_kwargs = {}

        trans = transition_t(
            state, *trans_args, targets=targets, **trans_kwargs
        )
        return trans.run(*args, **kwargs)


# class ResourceManagerBase(ABC):
#     """Base class for resource managers.
#     """
#     name = None
#     os_types = None
#     engine_types = None
#
#     @abstractmethod
#     def apply(self, resource: ResourceBase, new_state: Resource):
#         ...
#
#
# _MngrResp = attr.make_class(
#     "_MngrResp", ('engine', 'os_name'), frozen=True
# )
#
#
# class _ResourcesRegister(_Singletone):
#
#     def __init__(self):
#         self._resources = None
#         self._managers = None
#
#     def _load(self):
#         py_files = [
#             i for i in MODULE_DIR.glob('*.py')
#             if i.name not in (MODULE_PATH.name, '__init__.py')
#         ]
#
#         modules = [
#             importlib.import_module(f'{__package__}.{f.stem}')
#             for f in py_files
#         ]
#
#         resources = []
#         managers = []
#
#         for mod in modules:
#             for _attr_name in dir(mod):
#                 _attr = getattr(mod, _attr_name)
#
#                 for (base_cls, res) in [
#                     (ResourceBase, self.resources),
#                     (ResourceManagerBase, self.managers)
#                 ]:
#                     try:
#                         if not issubclass(_attr, base_cls):
#                             raise TypeError
#                     except TypeError:
#                         pass  # not a class or not a subclass of ResourceBase
#                     else:
#                         if _attr.name:
#                             res.append(_attr)
#                         else:
#                             logger.debug(
#                                 f"Ignoring resource class {_attr}: "
#                                 "undefined 'name'"
#                             )
#
#         self.resources = {comp.name: comp for comp in resources}
#         # TODO optimize: ranges
#         for mngr in managers:
#             self.managers = {
#                 _MngrResp(*resp): mngr
#                 for resp in itertools.product(
#                     mngr.eng_types,
#                     mngr.os_types
#                 )
#             }
#
#     @property
#     def resources(self):
#         if self._resources is None:
#             self._load()
#         return self._resources
#
#     def mananger(self, comp_t, engine, os_name):
#         if self._managers is None:
#             self._load()
#         return self.managers.get(_MngrResp(engine, os_name))
#
#     def reload(self):
#         self._load()
#
#
# COMPONENTS_REGISTER = _ResourcesRegister()
#
#
# @attr.s(auto_attribs=True)
# class SaltState:
#     """Base class for SaltStack resource state.
#
#     Attributes define set of pillar keys to parametrize salt state.
#
#     ...
#
#     Attributes
#     ----------
#
#     Methods
#     -------
#
#     Examples
#     --------
#
#     GlusterFS ''replaced'' state logic may require:
#
#     - old node role
#     - old node location (host)
#     - new node location
#     """
#     targets: str = ALL_MINIONS
#
#
# class SaltStackResourceManager(ABC):
#     """Base class for resource managers based on SaltStack. """
#     name = 'saltstack'
#     os_types = list(SetupOSType)
#     engine_types = [SetupEngineType.SALTSTACK]
#
#     def apply(self, resource: ResourceBase, new_state: ResourceState):
#         for pillar in new_state_attr_list:
#             pillar_set pillar
#         salt.state_apply(new_state.name, targets=new_state.targets)
#

# class DeployStage(ResourceState):
#     resource = None
#     stage = None
#     prefix = 'components'
#
#     @property
#     def state():
#         return f"{self.prefix}.{self.resource}.{self.stage}"
#
#
#
# @attr.s(auto_attribs=True)
# class ClusterResourceState(ResourceState):
#     resource_id: ClusterResourceID
#
#
# class SWManagerBase(ResourceManagerBase):
#
#     def setup(self, comp: Any, targets=ALL_MINIONS):
#         self.prepare(comp, targets)
#         self.install(comp, targets)
#         self.config(comp, targets)
#
#     @abstractmethod
#     def prepare(self, comp: Any, targets=ALL_MINIONS):
#         ...
#
#     @abstractmethod
#     def install(self, comp: Any, targets=ALL_MINIONS):
#         ...
#
#     @abstractmethod
#     def config(self, comp: Any, targets=ALL_MINIONS):
#         ...
#
#
# class ServiceManagerBase(SWManagerBase):
#
#     def setup(self, comp: Any, targets=ALL_MINIONS):
#         super().setup(comp, targets)
#         self.start(comp, targets)
#
#     @abstractmethod
#     def start(self, comp: Any, targets=ALL_MINIONS):
#         ...
#
#     @abstractmethod
#     def stop(self, comp: Any, targets=ALL_MINIONS):
#         ...
#
#
# class ClusteredServiceManagerBase(SWManagerBase):
#
#     def setup(self, comp: Any, targets=ALL_MINIONS):
#         super().setup(comp, targets)
#         self.join(comp, targets)
#
#     @abstractmethod
#     def join(self, comp: Any, targets=ALL_MINIONS):
#         self.start(comp, targets)
#         self.attach(comp, targets)
#
#     def attach(self, comp: Any, targets=ALL_MINIONS):
#         pass
#
#     @abstractmethod
#     def disconnect(self, comp: Any, targets=ALL_MINIONS):
#         self.detach(comp, targets)
#         self.stop(comp, targets)
#
#     def detach(self, comp: Any, targets=ALL_MINIONS):
#         pass
#
#
# # Note.
# #   - attach/detach makes sense only for active services (masters),
# #     clients might be just stopped
# class ClusterManagerBase(SWManagerBase):
#
#     def setup(self, comp: Any, targets=ALL_MINIONS):
#         super().setup(comp, targets)
#         self.join(comp, targets)
#
#     @abstractmethod
#     def join(self, comp: Any, targets=ALL_MINIONS):
#         self.start(comp, targets)
#         self.attach(comp, targets)
#
#     def attach(self, comp: Any, targets=ALL_MINIONS):
#         pass
#
#     @abstractmethod
#     def disconnect(self, comp: Any, targets=ALL_MINIONS):
#         self.detach(comp, targets)
#         self.stop(comp, targets)
#
#     def detach(self, comp: Any, targets=ALL_MINIONS):
#         pass
#
#
#
# entity manager (set): implies R
#     - no state
#     - api:            implies S
#         - install T
#         - config T
#         - start T
#         - stop T
#         - disconnect T
#
# cluster manager:
#     - structure:
#         - entity: T, R, S
#     - api:
#         - apply
#         - adjust(target:role)
