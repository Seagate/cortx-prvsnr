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

from ..vendor import attr
from utils import load_yaml

_mod = sys.modules[__name__]

logger = logging.getLogger(__name__)

attrs_spec = load_yaml(config.ATTRS_SPEC_PATH)


# CONVERTERS
def converter_path(value):
    return value if value is None else Path(str(value))


def converter_path_resolved(value):
    return value if value is None else Path(str(value)).resolve()


def converter_nodes(*specs):
    return [
        (s if isinstance(s, Node) else Node.from_spec(s))
        for s in specs
    ]


# VALIDATORS
def validator_path(instance, attribute, value):
    if value is None:
        if attribute.default is not None:
            raise ValueError(f"{attribute.name} should be defined")
    elif not isinstance(value, Path):
        raise TypeError(f"{attribute.name} should be a Path")


def validator_path_exists(instance, attribute, value):
    validator_path(instance, attribute, value)

    if value and not value.exists():
        raise ValueError(f"Path {value} doesn't exist")


VALIDATOR = 'validator'
CONVERTER = 'converter'

def attr_ib(key: str = None, **kwargs):
    if key:
        _kwargs = KeyPath(key).value(attrs_spec)
    else:
        _kwargs = {}

    _kwargs.update(kwargs)

    for fun_t in (CONVERTER, VALIDATOR):
        try:
            fun = _kwargs[fun_t]
        except KeyError:
            _kwargs[fun_t] = getattr(_mod, f'{fun_t}_{key}', None)
        else:
            _kwargs[fun_t] = getattr(_mod, f'{fun_t}_{fun}')

    cli_spec = _kwargs.pop('cli_spec')
    if cli_spec:
        _kwargs['metadata'] = _kwargs.pop('metadata', {})
        _kwargs['metadata'][inputs.METADATA_ARGPARSER] = cli_spec

    return attr.ib(**_kwargs)
