import sys
import attr
from typing import List, Dict, Type
from copy import deepcopy
import logging

from .config import ALL_MINIONS,PRVSNR_PILLAR_DIR
from .pillar import PillarUpdater, PillarResolver
from .api_spec import api_spec
from .salt import StatesApplier, State, YumRollbackManager
from provisioner import inputs

_mod = sys.modules[__name__]
logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsBase:
    targets: str = attr.ib(
        default=ALL_MINIONS,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "command's host targets"
            }
        }
    )


@attr.s(auto_attribs=True)
class RunArgsSSLCerts(RunArgsBase):
    restart: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "restart flag"
            }
        }, default=False
    )
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "ssl certs source"
            }
        }, default=False
    )


@attr.s(auto_attribs=True)
class RunArgsUpdate(RunArgsBase):
    dry_run: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "perform validation only"
            }
        }, default=False
    )


class CommandParserFillerMixin:
    _run_args_type = RunArgsBase

    @classmethod
    def fill_parser(cls, parser):
        inputs.ParserFiller.fill_parser(cls._run_args_type, parser)

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
class PillarGet(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams

    # TODO input class type
    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, targets: str = ALL_MINIONS):
        return PillarResolver(targets=targets).pillar


@attr.s(auto_attribs=True)
class Get(CommandParserFillerMixin):
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
class Set(CommandParserFillerMixin):
    # TODO at least either pre or post should be defined
    params_type: Type[inputs.ParamGroupInputBase]
    pre_states: List[State] = attr.Factory(list)
    post_states: List[State] = attr.Factory(list)

    _run_args_type = RunArgsUpdate

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
    def run(
        self, *args,
        targets: str = ALL_MINIONS, dry_run: bool = False, **kwargs
    ):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.params_type):
            params = args[0]
        else:
            params = self.params_type.from_args(*args, **kwargs)

        # TODO dynamic validation
        if dry_run:
            return

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


# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class EOSUpdate(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams

    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, targets):
        # TODO:
        #   - create a state instead
        #   - what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        with YumRollbackManager(targets, multiple_targets_ok=True):
            # TODO
            #  - update for provisioner itself
            #  - update for other sw ???
            for component in ('eoscore', 's3server', 'hare', 'sspl', 'csm'):
                state_name = "components.{}.update".format(component)
                try:
                    StatesApplier.apply([state_name])
                except Exception:
                    logger.exception(
                        "Failed to update {} on {}".format(component, targets)
                    )
                    raise

# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class SetSSLCerts(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSSLCerts
    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, *args, **kwargs):
        state_name = "components.build_ssl_certs"
        import pdb;pdb.set_trace()
        PRVSNR_PILLAR_DIR
        try:
            StatesApplier.apply([state_name])
        except Exception:
            logger.exception(
                "Failed to apply certs {} on {}".format(component, targets)
            )
            raise

commands = {}
for command_name, spec in api_spec.items():
    spec = deepcopy(api_spec[command_name])  # TODO
    command = getattr(_mod, spec.pop('type'))
    commands[command_name] = command.from_spec(**spec)
