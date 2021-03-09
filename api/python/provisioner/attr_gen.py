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

from ..vendor import attr
from . import utils
from . import config, inputs
from .node import Node
from .pillar import KeyPath

_mod = sys.modules[__name__]

logger = logging.getLogger(__name__)

attrs_spec = utils.load_yaml(config.ATTRS_SPEC_PATH)


# CONVERTERS FIXME move here from utils
def converter__path(value):
    return utils.converter_path(value)


def converter__path_resolved(value):
    return utils.converter__path_resolved(value)


def converter__nodes(*specs):
    return [
        (s if isinstance(s, Node) else Node.from_spec(s))
        for s in specs
    ]


# VALIDATORS
def validator__path(instance, attribute, value):
    utils.validator_path(instance, attribute, value)


def validator__path_exists(instance, attribute, value):
    utils.validator_path_exists(instance, attribute, value)


def validator__subclass_of(instance, attribute, value):
    utils.validator__subclass_of(instance, attribute, value)


VALIDATOR = 'validator'
CONVERTER = 'converter'
SEP = '__'


def attr_ib(key: str = None, **kwargs):
    _kwargs = {}

    if key:
        _kwargs = KeyPath(key).value(attrs_spec)

    _kwargs.update(kwargs)

    for fun_t in (CONVERTER, VALIDATOR):
        try:
            fun = _kwargs[fun_t]
        except KeyError:
            # to support validators named as a key
            _kwargs[fun_t] = getattr(_mod, f'{fun_t}{SEP}{key}', None)
        else:
            # to support validators explicitly defined
            _kwargs[fun_t] = getattr(_mod, f'{fun_t}{SEP}{fun}')

    cli_spec = _kwargs.pop('cli_spec')
    if cli_spec:
        _kwargs['metadata'] = _kwargs.pop('metadata', {})
        _kwargs['metadata'][inputs.METADATA_ARGPARSER] = cli_spec

    return attr.ib(**_kwargs)
