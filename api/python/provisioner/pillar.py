import sys
import logging
import attr
from typing import Any, List, Dict, Union, Tuple
from copy import deepcopy
from pathlib import Path

from .utils import load_yaml, dump_yaml
from .salt import pillar_get, pillar_refresh
from .param import KeyPath, Param
from .config import (
    ALL_MINIONS,
    PRVSNR_USER_PI_ALL_HOSTS_DIR,
    PRVSNR_USER_PI_HOST_DIR_TMPL
)
from .inputs import ParamGroupInputBase, ParamDictItemInputBase
from .values import UNCHANGED, DEFAULT, MISSED, UNDEFINED

logger = logging.getLogger(__name__)

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
    _pillar: Dict = None

    @property
    def pillar(self):
        if self._pillar is None:
            self._pillar = pillar_get(targets=self.targets)
        return self._pillar

    def get(self, params: List[Param]):  # TODO return value
        # TODO provide results per target
        # - for now just use the first target's pillar value
        res = {}
        for minion_id, pillar in self.pillar.items():
            res[minion_id] = {
                p: PillarEntry(p.pi_key, pillar).get() for p in params
            }
        return res


# TODO verify that targets are resoloved to real minions
# TODO for now targeting supports either ALL or one single,
#      need to support any syntax that salt supports, option:
#      - convert any targets string to list of minions using
#        call to the salt
@attr.s(auto_attribs=True)
class PillarUpdater:
    targets: str = ALL_MINIONS
    _pillars: Dict = attr.Factory(dict)
    _p_entries: List[PillarEntry] = attr.Factory(list)

    def ensure_exists(self, path: Path):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

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
            _path = PRVSNR_USER_PI_ALL_HOSTS_DIR / path
        else:
            _path = Path(
                PRVSNR_USER_PI_HOST_DIR_TMPL.format(minion_id=self.targets)
            ) / path

        if _path not in self._pillars:
            self._pillars[_path] = load_yaml(_path) if _path.exists() else {}
        return self._pillars[_path]

    def update(
        self,
        *params: Tuple[Union[ParamGroupInputBase, ParamDictItemInputBase], ...]
    ) -> None:
        if self._p_entries:
            logger.error("RuntimeError: Update already started")
            #raise RuntimeError("Update already started")

        for data in params:
            for param, value in data:
                p_entry = PillarEntry(param.pi_key, self.pillar(param.pi_path))

                if value is not UNCHANGED:
                    if value is MISSED:
                        logger.error(
                              "ValueError: Total removal of a pillar entry is not allowed, key_path: {}"
                              .format(p_entry.key_path)
                        )
                        #raise ValueError(
                        #    "Total removal of a pillar entry is not allowed, "
                        #    "key_path: {}"
                        #    .format(p_entry.key_path)
                        #)

                    if value is UNDEFINED:
                        value = None
                    elif value is DEFAULT:
                        # TODO create task: requires pillar re-structuring to
                        #      get the value from pillar files since a call
                        #      to pillar.items can't help here
                        logger.error(
                              "NotImplementedError: Reset to factory default is not yet supported,key_path: {}"
                              .format(p_entry.key_path)
                        )
                        #raise NotImplementedError(
                        #    "Reset to factory default is not yet supported, "
                        #    "key_path: {}"
                        #    .format(p_entry.key_path)
                        #)

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
    def apply(self) -> None:
        self.dump()
        self.refresh(self.targets)

    @staticmethod
    def refresh(targets: str = ALL_MINIONS):
        return pillar_refresh(targets=targets)
