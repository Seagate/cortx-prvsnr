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
    targets: str = attr.ib(kw_only=True, default=ALL_TARGETS)

    # XXX need abstraction for targets:
    #     - different SCM might use different aliases for all targets,
    #       different bulk targeting (lists, globs, regex ...)
    @abstractmethod
    def run(self):
        """Move a resource to a state."""


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
