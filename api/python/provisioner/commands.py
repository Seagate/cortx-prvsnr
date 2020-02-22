import sys
import attr
from typing import List, Dict, Type
from copy import deepcopy
import logging

from .config import ALL_MINIONS
from .pillar import PillarUpdater, PillarResolver
from .api_spec import api_spec
from .salt import StatesApplier, State
from provisioner import inputs

_mod = sys.modules[__name__]
logger = logging.getLogger(__name__)


#  - Notes:
#       1. call salt pillar is good since salt will expand
#          properly pillar itself
#       2. if pillar != system state then we are bad
#           - then assume they are in-sync
#  - ? what are cases when pillar != system
#  - ? options to check/ensure sync:
#     - salt.mine
#     - periodical states apply
@attr.s(auto_attribs=True)
class PillarGet:
    params_type: Type[inputs.NoParams] = inputs.NoParams

    # TODO input class type
    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, targets: str = ALL_MINIONS):
        return PillarResolver(targets=targets).pillar


@attr.s(auto_attribs=True)
class Get:
    params_type: Type[inputs.ParamsList] = inputs.ParamsList

    # TODO input class type
    @classmethod
    def from_spec(
        cls, params_type: str = 'ParamsList'
    ):
        return cls(params_type=getattr(inputs, params_type))

    def run(self, *args, targets: str = ALL_MINIONS, **kwargs):
        params = self.params_type.from_args(*args, **kwargs)
        pillar_resolver = PillarResolver(targets=targets)
        res_raw = pillar_resolver.get(params)
        res = {}
        for minion_id, data in res_raw.items():
            res[minion_id] = {str(p.name): v for p, v in data.items()}
        return res


# TODO
#   - how to support targetted pillar
#       - per group (grains)
#       - per minion
#       - ...
@attr.s(auto_attribs=True)
class Set:
    # TODO at least either pre or post should be defined
    params_type: Type[inputs.ParamGroupInputBase]
    pre_states: List[State] = attr.Factory(list)
    post_states: List[State] = attr.Factory(list)

    # TODO input class type
    @classmethod
    def from_spec(
        cls, params_type: str, states: Dict
    ):
        return cls(
            params_type=getattr(inputs, params_type),
            pre_states=[State(state) for state in states.get('pre', [])],
            post_states=[State(state) for state in states.get('post', [])]
        )

    # TODO
    # - class for pillar file
    # - caching (load once)
    def run(self, *args, targets: str = ALL_MINIONS, **kwargs):
        if len(args) == 1 and isinstance(args[0], self.params_type):
            params = args[0]
        else:
            params = self.params_type.from_args(*args, **kwargs)

        pillar_updater = PillarUpdater(targets)

        pillar_updater.update(params)
        try:
            StatesApplier.apply(self.pre_states)
            try:
                pillar_updater.apply()
                StatesApplier.apply(self.post_states)
            except Exception:
                # TODO more solid rollback
                pillar_updater.rollback()
                pillar_updater.apply()
                raise
        except Exception:
            # treat post as restoration for pre, apply
            # if rollback happened
            StatesApplier.apply(self.post_states)
            raise


@attr.s(auto_attribs=True)
class EOSUpdate:
    params_type: Type[inputs.NoParams] = inputs.NoParams

    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, targets: str = ALL_MINIONS):
        # TODO
        #  - rollback
        #  - update for provisioner itself
        #  - update for other sw ???
        for component in ('eoscore', 's3server', 'hare', 'sspl', 'csm'):
            state_name = "components.{}.update".format(component)
            logger.info("Applying state {}".format(state_name))
            StatesApplier.apply([state_name])


commands = {}
for command_name, spec in api_spec.items():
    spec = deepcopy(api_spec[command_name])  # TODO
    command = getattr(_mod, spec.pop('type'))
    commands[command_name] = command.from_spec(**spec)
