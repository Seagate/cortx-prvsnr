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

from typing import Union, Tuple
from pathlib import Path

from .vendor import attr
from .pillar import KeyPath, PillarKeyAPI, PillarKey


# TODO TEST
# TODO explore more options of hashing
# (http://www.attrs.org/en/stable/hashing.html)
@attr.s(auto_attribs=True, frozen=True)
class Param(PillarKeyAPI):
    name: KeyPath = attr.ib(converter=KeyPath)
    _pi_key: Union[PillarKey, str, Tuple[str, str]] = attr.ib(
        converter=(
            lambda k: (
                PillarKey(str(k)) if isinstance(k, (str, Path, KeyPath)) else
                PillarKey(*k) if type(k) is tuple else
                k
            )
        ),
        validator=attr.validators.instance_of(PillarKey)
    )

    @property
    def keypath(self):
        return self._pi_key.keypath

    @property
    def fpath(self):
        return self._pi_key.fpath

    def __str__(self):
        return str(self.name)


@attr.s(auto_attribs=True, frozen=True)
class ParamDictItem(Param):
    key: str = 'pillar_key'
    value: str = 'pillar_value'

    @classmethod
    def from_spec(cls, name, parent, _path, **kwargs):
        return cls(
            name, pi_key=PillarKey(fpath=_path, keypath=parent), **kwargs
        )
