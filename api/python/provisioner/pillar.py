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
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Tuple, Iterable, Union, Optional
from copy import deepcopy
from pathlib import Path

from . import values
from .errors import BadPillarDataError
from .vendor import attr
from .utils import load_yaml, dump_yaml
from .salt import pillar_get, pillar_refresh
from .config import (
    ALL_MINIONS,
    PRVSNR_PILLAR_DIR
)
from .paths import (
    PillarPath,
    USER_SHARED_PILLAR,
    USER_LOCAL_PILLAR
)

# from .salt_api import SaltClientBase
# from .inputs import ParamGroupInputBase, ParamDictItemInputBase
from .values import UNCHANGED, DEFAULT, MISSED, UNDEFINED

logger = logging.getLogger(__name__)


# TODO explore more options of hashing
# (http://www.attrs.org/en/stable/hashing.html)
@attr.s(auto_attribs=True, frozen=True)
class KeyPath:
    # TODO DOC good way of converter - validator combination
    _path: Path = attr.ib(
        converter=(lambda v: None if v is None else Path(str(v))),
        validator=attr.validators.instance_of(Path)
    )

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


class PillarKeyAPI(ABC):
    @property
    def keypath(self):
        pass

    @property
    def fpath(self):
        pass


# TODO explore more options of hashing
# (http://www.attrs.org/en/stable/hashing.html)
@attr.s(auto_attribs=True, frozen=True)
class PillarKey(PillarKeyAPI):
    _keypath: Union[KeyPath, str] = attr.ib(converter=KeyPath)
    _fpath: Path = attr.ib(
        converter=(lambda p: Path(str(p)) if p else p),
        default=None
    )

    def __attrs_post_init__(self):
        # TODO IMPROVE add validator instead
        keypath = Path(str(self._keypath))
        parents = keypath.parents
        if not len(parents):
            raise ValueError(f"keypath {keypath} is incorrect")

        # <top-level-parent>.sls
        if self._fpath is None:
            fname = (
                keypath if len(parents) == 1 else parents[len(parents) - 2]
            ).name
            # Note. a documented workaround:
            #   https://www.attrs.org/en/stable/init.html#post-init-hook
            object.__setattr__(
                self, '_fpath', Path(
                    f"{fname}.sls"
                )
            )

    @property
    def keypath(self):
        return self._keypath

    @property
    def fpath(self):
        return self._fpath

    def __str__(self):
        return str(self.keypath)


class PillarItemsAPI(ABC):
    @abstractmethod
    def pillar_items(self) -> Iterable[Tuple[PillarKeyAPI, Any]]:
        ...


@attr.s(auto_attribs=True)
class PillarIterable(PillarItemsAPI):
    # XXX better typing: for List and Tuple (path, value) items are expected
    pi_items: Union[Dict, List, Tuple]
    # file path relative to pillar roots,
    # if not specified <key-path-top-level-part>.sls
    # for each pillar item would be used'
    fpath: Optional[str] = None

    _pillars: Dict[PillarKey, Any] = attr.Factory(dict)

    def __attrs_post_init__(self):
        if isinstance(self.pi_items, Dict):
            self._pillars = {
                PillarKey(k, fpath=self.fpath): v
                for k, v in self.pi_items.items()
            }
        elif isinstance(List, Tuple):
            self._pillars = {
                PillarKey(i[0], fpath=self.fpath): i[1]
                for i in self.pi_items
            }
        else:
            raise TypeError(
                f"unxpected type of 'pi_items': '{type(self.pi_items)}'"
            )

    def pillar_items(self) -> Iterable[Tuple[PillarKeyAPI, Any]]:
        return tuple(self._pillars.items())


@attr.s(auto_attribs=True)
class PillarEntry:
    key_path: KeyPath = attr.ib(converter=KeyPath)
    pillar: Dict = attr.Factory(dict)
    _old_value_exists: bool = None
    _old_value: Any = None  # TODO

    def get(self) -> Any:  # TODO
        try:
            return self.key_path.value(self.pillar)
        except KeyError:
            return MISSED

    def set(self, value: Any) -> None:
        if self._old_value_exists is not None:
            return

        parent_dict = self.key_path.parent_dict(self.pillar)
        leaf = self.key_path.leaf

        # REMEMBER OLD VALUE
        if leaf in parent_dict:
            self._old_value_exists = True
            self._old_value = deepcopy(parent_dict[leaf])
        else:
            self._old_value_exists = False

        # UPDATE PILLAR DATA IN-MEMORY
        parent_dict[leaf] = value

    def rollback(self) -> None:
        if self._old_value_exists is None:
            return

        parent_dict = self.key_path.parent_dict(
            self.pillar, fix_missing=False
        )
        if self._old_value_exists:
            parent_dict[self.key_path.leaf] = self._old_value
        else:
            del parent_dict[self.key_path.leaf]


@attr.s(auto_attribs=True)
class PillarResolver:
    targets: str = ALL_MINIONS
    local: bool = False
    _pillar: Dict = None

    @property
    def pillar(self):
        if self._pillar is None:
            self._pillar = pillar_get(
                targets=self.targets, local=self.local
            )
        return self._pillar

    # TODO return value
    def get(
        self,
        pi_keys: Iterable[PillarKeyAPI],
        fail_on_undefined: bool = False
    ):
        # TODO provide results per target
        # - for now just use the first target's pillar value
        res = {}
        for minion_id, pillar in self.pillar.items():
            res[minion_id] = {
                pk: PillarEntry(pk.keypath, pillar).get() for pk in pi_keys
            }

        if fail_on_undefined:
            for node_id, pillar in res.items():
                for pk in pi_keys:
                    if not pillar[pk] or pillar[pk] is values.MISSED:
                        raise BadPillarDataError(
                            f"value for {pk.keypath} is not specified "
                            f"for node {node_id}"
                        )

        return res


# FIXME EOS-15022 rename once tested enough
@attr.s(auto_attribs=True)
class PillarResolverNew(PillarResolver):
    # FIXME EOS-15022 cross import issue
    # client: SaltClientBase = None
    client: Any = None

    @property
    def pillar(self):
        if self._pillar is None:
            if self.client is None:
                self._pillar = pillar_get(
                    targets=self.targets, local=self.local
                )
            else:
                # TODO IMPROVE optional targetting should
                #      be taken care only inside client parameters
                #      for now
                self._pillar = self.client.pillar_get(targets=self.targets)
        return self._pillar


# TODO verify that targets are resoloved to real minions
# TODO for now targeting supports either ALL or one single,
#      need to support any syntax that salt supports, option:
#      - convert any targets string to list of minions using
#        call to the salt
@attr.s(auto_attribs=True)
class PillarUpdater:
    targets: str = ALL_MINIONS
    local: bool = False

    _pillar_path: PillarPath = attr.ib(init=False, default=None)
    _pillars: Dict = attr.Factory(dict)
    _p_entries: List[PillarEntry] = attr.Factory(list)

    def __attrs_post_init__(self):
        self._pillar_path = (
            USER_LOCAL_PILLAR if self.local else USER_SHARED_PILLAR
        )

    @staticmethod
    def ensure_exists(path: Path):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    @classmethod
    def add_merge_prefix(cls, path: Path, local=False):
        pillar_path = (
            USER_LOCAL_PILLAR if local else USER_SHARED_PILLAR
        )

        if path.name.startswith(pillar_path.prefix):
            return path
        else:
            return path.with_name(f"{pillar_path.prefix}{path.name}")

    # TODO create task
    # TODO test
    # base things:
    #       - group values are defaults for group memebers
    #       - minion values override any group ones
    #
    #       - group vs minion vars challenges:
    #           - setting a value for a group, goals options:
    #
    #             1) update group defaults
    #               -> update only group vars
    #               -> a memeber will have the value only if key is missed
    #                  in minion vars and any other more prioritized groups
    #             2) update key for all members
    #               -> update group vars along with minion vars for all members
    #               -> all hosts in that group will receive that value
    #               -> BUT it may shift settings from point of view
    #                  of a minion's other groups
    #
    #           - reseting user value (to a default factory one) for a group,
    #             goals options:
    #
    #             1) reset only group defaults
    #               -> reset only group vars
    #               -> a memeber will have the factory default only if key is
    #                  missed in minion vars and any other more prioritized
    #                  groups
    #             2) reset key for all members
    #               -> reset the group vars along with minion vars for all
    #                  members
    #               -> BUT minion will get factory default only if the key is
    #                  missed in all other its groups
    #
    #           - THUS:
    #               - safer and simplier to use group vars updates only
    #                 for groups defaults shifting, groups members values
    #                 update is not guaranteed
    #               - any guaranteed updates for minions require updates
    #                 in their minion vars:
    #                   - reset as a special case turns into update with
    #                     factory default value
    #
    # cases: combination of targets and values
    #   targets:
    #       1. group ('all' is special since its memeber are known initially)
    #       2. a minion
    #   values:
    #       1. UNCHANGED (no action needed)
    #       2. DEFAULT
    #       3. UNDEFINED
    #       4. MISSED (not allowed, for get queries only)
    #       5. value: any other non special value
    #   combinations:
    #       1-2. group-DEFAULT: set factory default for a group
    #       1-3. group-UNDEFINED: make value undefined for a group
    #       1-5. group-value: set value for a group
    #       2-2. minion-DEFAULT: set factory default for a minion
    #            (a merge result of factory settings for minion and
    #             all is group vars) ??? TODO
    #       2-3. minion-UNDEFINED: make value undefined for a minion
    #       2-5. minion-value: set value for a minion
    def pillar(self, path: Path):
        if self.targets == ALL_MINIONS:
            _path = self._pillar_path.all_hosts_dir / path
        else:
            _path = Path(
                self._pillar_path.host_dir_tmpl.format(minion_id=self.targets)
            ) / path

        _path = self.add_merge_prefix(_path, local=self.local)

        if _path not in self._pillars:
            self._pillars[_path] = load_yaml(_path) if _path.exists() else {}
        return self._pillars[_path]

    # TODO IMPROVE add option to verify updated pillar
    #      (resolve actual pillar data after update)
    def update(self, *pi_groups: Tuple[PillarItemsAPI, ...]) -> None:
        if self._p_entries:
            logger.error("Update already started")
            raise RuntimeError("Update already started")

        for pi_group in pi_groups:
            for pi_key, value in pi_group.pillar_items():
                p_entry = PillarEntry(
                    pi_key.keypath, self.pillar(pi_key.fpath)
                )

                if value is not UNCHANGED:
                    if value is MISSED:
                        logger.error(
                              "Total removal of a pillar "
                              "entry is not allowed, "
                              "key_path: {}"
                              .format(p_entry.key_path)
                        )
                        raise ValueError(
                            "Total removal of a pillar entry is not allowed, "
                            "key_path: {}"
                            .format(p_entry.key_path)
                        )

                    if value is UNDEFINED:
                        value = None
                    elif value is DEFAULT:
                        # TODO create task: requires pillar re-structuring to
                        #      get the value from pillar files since a call
                        #      to pillar.items can't help here
                        logger.error(
                              "Reset to factory default "
                              "is not yet supported, key_path: {}"
                              .format(p_entry.key_path)
                        )
                        raise NotImplementedError(
                            "Reset to factory default is not yet supported, "
                            "key_path: {}"
                            .format(p_entry.key_path)
                        )

                    p_entry.set(value)

                # register an entry in any valid case to mark update started
                self._p_entries.append(p_entry)

    def rollback(self) -> None:
        # TODO might be safe without list()
        for p_entry in list(self._p_entries[::-1]):
            p_entry.rollback()
            self._p_entries.pop()

    def dump(self) -> None:
        for path, pillar in self._pillars.items():
            self.ensure_exists(path)
            dump_yaml(path, pillar)

    # TODO test
    def apply(self, rollback_on_error=False) -> None:
        try:
            self.dump()
            if not self.local:
                self.refresh(self.targets)
        except Exception:
            if rollback_on_error:
                self.rollback()
                self.apply(rollback_on_error=False)
            raise

    @staticmethod
    def refresh(targets: str = ALL_MINIONS):
        return pillar_refresh(targets=targets)

    @classmethod
    def component_pillar(
        cls,
        component,
        show: bool = False,
        reset: bool = False,
        pillar: Dict = None
    ):
        # NOTE only shared dir is considered (possibly not always ok)
        path = (
            USER_SHARED_PILLAR / '{}.sls'.format(component)
        )
        if show:
            if not path.exists():
                path = (
                    PRVSNR_PILLAR_DIR / 'components' /
                    '{}.sls'.format(component)
                )
            return load_yaml(path)
        elif reset:
            if path.exists():
                path.unlink()
        elif pillar:
            cls.ensure_exists(path)
            dump_yaml(path, pillar)


# FIXME EOS-15022 rename once tested enough
@attr.s(auto_attribs=True)
class PillarUpdaterNew(PillarUpdater):
    pillar_path: PillarPath = USER_SHARED_PILLAR
    client: Any = None

    def __attrs_post_init__(self):
        if self.local:
            self.pillar_path = USER_LOCAL_PILLAR
        # XXX FIXME patch
        if not self.client:
            raise ValueError('client should be specified')

    @classmethod
    def add_merge_prefix(cls, path: Path, local=False):
        pillar_path = (
            USER_LOCAL_PILLAR if local else USER_SHARED_PILLAR
        )

        if path.name.startswith(pillar_path.prefix):
            return path
        else:
            return path.with_name(f"{pillar_path.prefix}{path.name}")

    def pillar(self, path: Path):
        if self.targets == ALL_MINIONS:
            _path = self.pillar_path.all_hosts_path(path)
        else:
            _path = self.pillar_path.host_path(path, self.targets)

        if _path not in self._pillars:
            self._pillars[_path] = load_yaml(_path) if _path.exists() else {}
        return self._pillars[_path]

    def refresh(self, targets: str = ALL_MINIONS):
        return self.client.pillar_refresh(targets=targets)
