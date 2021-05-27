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

import sys
import logging
from typing import (
    Tuple, Union, Type, Any, Callable, Optional, List
)
from ipaddress import IPv4Address
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from provisioner.vendor import attr

from . import utils
from . import config, inputs
from .node import Node
from .pillar import KeyPath

_mod = sys.modules[__name__]

logger = logging.getLogger(__name__)

VALIDATOR = 'validator'
CONVERTER = 'converter'
SEP = '__'


# CONVERTERS FIXME move here from utils
def converter__path(value):
    return utils.converter_path(value)


def converter__path_resolved(value):
    return utils.converter_path_resolved(value)


def converter__nodes(*specs):
    return [
        (s if isinstance(s, Node) else Node.from_spec(s))
        for s in specs
    ]


def converter__version(value):
    return (
        value if value is None or isinstance(value, Version)
        else Version(value)
    )


def converter__version_specifier(value):
    return value if isinstance(value, SpecifierSet) else SpecifierSet(value)


def converter__ipv4(value) -> IPv4Address:
    return IPv4Address(value)


def converter__special_values(
    values: Union[Tuple, List],
    orig_converter: Optional[Callable] = None
) -> Callable:

    def _f(value):
        if (value in values) or (orig_converter is None):
            return value
        else:
            return orig_converter(value)

    return _f


# VALIDATORS
def validator__path(instance, attribute, value):
    utils.validator_path(instance, attribute, value)


def validator__path_exists(instance, attribute, value):
    utils.validator_path_exists(instance, attribute, value)


def validator__subclass_of(
        subclass: Union[Type[Any], Tuple[Type[Any], ...]]) -> Callable:
    utils.validator__subclass_of(subclass)


def validator__version(instance, attribute, value):
    return attr.validators.instance_of(Version)(instance, attribute, value)


def validator__ipv4(instance, attribute, value):
    return attr.validators.instance_of(IPv4Address)(instance, attribute, value)


def validator__version_specifier(instance, attribute, value):
    return attr.validators.instance_of(SpecifierSet)(
        instance, attribute, value
    )


def load_attrs_spec():
    res = utils.load_yaml(config.ATTRS_SPEC_PATH)

    for attr_t in res:
        for fun_t in (CONVERTER, VALIDATOR):
            try:
                fun = res[attr_t][fun_t]
            except KeyError:
                # to support functions named as a key
                res[attr_t][fun_t] = getattr(
                    _mod, f'{fun_t}{SEP}{attr_t}', None
                )
            else:
                # to support functions explicitly defined
                res[attr_t][fun_t] = getattr(_mod, f'{fun_t}{SEP}{fun}')

    return res


def validator__special_values(
    values: Union[Tuple, List],
    orig_validator: Optional[Callable] = None
) -> Callable:

    def _f(instance, attribute, value):
        if (value not in values) and orig_validator:
            orig_validator(instance, attribute, value)

    return _f


attrs_spec = load_attrs_spec()


# key - a reference to prefedined attr spec
# special_values - values that don't need default converter or validator
def attr_ib(key: str = None, special_values: Optional[List] = None, **kwargs):
    _kwargs = {}

    if key:
        _kwargs = KeyPath(key).value(attrs_spec)
        if special_values:
            _kwargs[CONVERTER] = converter__special_values(
                special_values, _kwargs.get(CONVERTER)
            )
            _kwargs[VALIDATOR] = validator__special_values(
                special_values, _kwargs.get(VALIDATOR)
            )

    _kwargs.update(kwargs)

    cli_spec = _kwargs.pop('cli_spec', None)
    if cli_spec:
        _kwargs['metadata'] = _kwargs.pop('metadata', {})
        _kwargs['metadata'][inputs.METADATA_ARGPARSER] = cli_spec

    return attr.ib(**_kwargs)
