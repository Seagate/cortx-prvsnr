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
    return (value if isinstance(value, Version) else Version(value))


def converter__version_specifier(value):
    return (value if isinstance(value, SpecifierSet) else SpecifierSet(value))


# VALIDATORS
def validator__path(instance, attribute, value):
    utils.validator_path(instance, attribute, value)


def validator__path_exists(instance, attribute, value):
    utils.validator_path_exists(instance, attribute, value)


def validator__subclass_of(instance, attribute, value):
    utils.validator__subclass_of(instance, attribute, value)


def validator__version(instance, attribute, value):
    return attr.validators.instance_of(Version)(instance, attribute, value)


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


attrs_spec = load_attrs_spec()


def attr_ib(key: str = None, **kwargs):
    _kwargs = {}

    if key:
        _kwargs = KeyPath(key).value(attrs_spec)

    _kwargs.update(kwargs)

    cli_spec = _kwargs.pop('cli_spec', None)
    if cli_spec:
        _kwargs['metadata'] = _kwargs.pop('metadata', {})
        _kwargs['metadata'][inputs.METADATA_ARGPARSER] = cli_spec

    return attr.ib(**_kwargs)
