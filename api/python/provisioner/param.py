import attr
from typing import Dict
from pathlib import Path

# TODO explore more options of hashing
# (http://www.attrs.org/en/stable/hashing.html)
@attr.s(auto_attribs=True, frozen=True)
class KeyPath:
    _path: Path = attr.ib(converter=lambda v: Path(str(v)))

    def __str__(self):
        return str(self._path)

    def __truediv__(self, key):
        return KeyPath(self._path / key)

    def parent_dict(self, key_dict: Dict, fix_missing=True):
        res = key_dict
        for key in self._path.parts[:-1]:  # TODO optimize
            # ensure key exists
            if key not in res:
                if fix_missing:
                    res[key] = {}
            res = res[key]
        return res

    @property
    def parent(self):
        return KeyPath(self._path.parent)

    @property
    def leaf(self):
        return self._path.name

    def value(self, key_dict: Dict):
        return self.parent_dict(key_dict, fix_missing=False)[self.leaf]


# TODO explore more options of hashing
# (http://www.attrs.org/en/stable/hashing.html)
@attr.s(auto_attribs=True, frozen=True)
class Param:
    name: KeyPath = attr.ib(converter=KeyPath)
    pi_path: Path = attr.ib(converter=Path)
    pi_key: KeyPath = attr.ib(converter=KeyPath)

    def __str__(self):
        return str(self.name)


@attr.s(auto_attribs=True, frozen=True)
class ParamDictItem(Param):
    key: str
    value: str

    @classmethod
    def from_spec(cls, name, parent, key, value, _path):
        return cls(name, pi_path=_path, pi_key=parent, key=key, value=value)
