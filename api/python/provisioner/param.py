import attr
from typing import Union, Tuple
from pathlib import Path

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
