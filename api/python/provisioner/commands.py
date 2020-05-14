import sys
import attr
from typing import List, Dict, Type, Union
from copy import deepcopy
import logging
from datetime import datetime
from pathlib import Path

from .errors import (
    BadPillarDataError,
    SWUpdateError,
    SWUpdateFatalError,
    ClusterMaintenanceEnableError,
    SWStackUpdateError,
    ClusterMaintenanceDisableError
)
from .config import (
    ALL_MINIONS, PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR,
    PRVSNR_FILEROOTS_DIR, LOCAL_MINION,
    PRVSNR_USER_FILES_SSL_CERTS_FILE,
    PRVSNR_EOS_COMPONENTS,
    CONTROLLER_BOTH,
    SSL_CERTS_FILE
)
from .utils import load_yaml, dump_yaml_str
from .param import KeyPath, Param
from .pillar import PillarUpdater, PillarResolver
from .api_spec import api_spec
from .salt import (
    StatesApplier, StateFunExecuter, State,
    YumRollbackManager,
    SaltJobsRunner, function_run,
    copy_to_file_roots
)
from .hare import (
    cluster_maintenance_enable, cluster_maintenance_disable
)
from .salt_master import (
    config_salt_master, ensure_salt_master_is_running
)
from .salt_minion import config_salt_minions
from provisioner import inputs
from provisioner import values

_mod = sys.modules[__name__]
logger = logging.getLogger(__name__)


class RunArgs:
    targets: str = attr.ib(
        default=ALL_MINIONS,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "command's host targets"
            }
        }
    )
    dry_run: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "perform validation only"
            }
        }, default=False
    )


@attr.s(auto_attribs=True)
class RunArgsEmpty:
    pass


@attr.s(auto_attribs=True)
class RunArgsBase:
    targets: str = RunArgs.targets


@attr.s(auto_attribs=True)
class RunArgsUpdate:
    targets: str = RunArgs.targets
    dry_run: bool = RunArgs.dry_run

# TODO DRY
@attr.s(auto_attribs=True)
class RunArgsFWUpdate:
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "a path to FW update"
            }
        }
    )
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class RunArgsGetResult:
    cmd_id: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "provisioner command ID"
            }
        }
    )


@attr.s(auto_attribs=True)
class RunArgsSSLCerts:
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "ssl certs source"
            }
        }
    )
    restart: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "restart flag"
            }
        }, default=False
    )
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class RunArgsConfigureEOS:
    component: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "EOS component to configure",
                'choices': PRVSNR_EOS_COMPONENTS
            }
        }
    )
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "a yaml file to apply"
            }
        },
        default=None
    )
    show: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "dump current configuration"
            }
        }, default=False
    )
    reset: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "reset configuration to the factory state"
            }
        }, default=False
    )


@attr.s(auto_attribs=True)
class RunArgsController:
    target_ctrl: str = attr.ib(
        default=CONTROLLER_BOTH,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "target controller"
                # TODO IMPROVE use argparse choises to limit
                #      valid vales only to a/b/both
            }
        }
    )


class CommandParserFillerMixin:
    _run_args_type = RunArgsBase

    @classmethod
    def fill_parser(cls, parser):
        inputs.ParserFiller.fill_parser(cls._run_args_type, parser)

    @classmethod
    def from_spec(cls):
        return cls()

    @classmethod
    def extract_positional_args(cls, kwargs):
        return inputs.ParserFiller.extract_positional_args(
            cls._run_args_type, kwargs
        )


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

    def run(self, *args, targets=ALL_MINIONS, **kwargs):
        # TODO tests
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
#
# Implements the following:
#   - update pillar related to some param(s)
#   - call related states (before and after)
#   - rollback if something goes wrong
@attr.s(auto_attribs=True)
class Set(CommandParserFillerMixin):
    # TODO at least either pre or post should be defined
    params_type: Type[
        Union[inputs.ParamGroupInputBase, inputs.ParamDictItemInputBase]
    ]
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

    def _run(self, params, targets):
        pillar_updater = PillarUpdater(targets)

        pillar_updater.update(params)
        try:
            StatesApplier.apply(self.pre_states)
            try:
                pillar_updater.apply()
                StatesApplier.apply(self.post_states)
            except Exception:
                logger.exception('Failed to apply changes')
                # TODO more solid rollback
                pillar_updater.rollback()
                pillar_updater.apply()
                raise
        except Exception:
            logger.exception('Failed to apply changes')
            # treat post as restoration for pre, apply
            # if rollback happened
            StatesApplier.apply(self.post_states)
            raise

    # TODO
    # - class for pillar file
    # - caching (load once)
    def run(self, *args, targets=ALL_MINIONS, dry_run=False, **kwargs):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.params_type):
            params = args[0]
        else:
            params = self.params_type.from_args(*args, **kwargs)

        # TODO dynamic validation
        if dry_run:
            return

        self._run(params, targets)


# assumtions / limitations
#   - support only for ALL_MINIONS targetting TODO ??? why do you think so
#
#

# set/remove the repo:
#   - call repo reset logic for minions:
#       - remove repo config for yum
#       - unmount repo if needed
#       - remove repo dir/iso file if needed TODO
#   - call repo reset logic for master:
#       - remove local dir/file from salt user file root (if needed)
@attr.s(auto_attribs=True)
class SetEOSUpdateRepo(Set):
    # TODO at least either pre or post should be defined
    params_type: Type[inputs.EOSUpdateRepo] = inputs.EOSUpdateRepo

    # TODO rollback
    def _run(self, params: inputs.EOSUpdateRepo, targets: str):
        # if local - copy the repo to salt user file root
        # TODO consider to use symlink instead
        if params.is_local():
            dest = PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR / params.release

            if not params.is_dir():  # iso file
                dest = dest.with_name(dest.name + '.iso')

            copy_to_file_roots(params.source, dest)

        # call default set logic (set pillar, call related states)
        super()._run(params, targets)


# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class EOSUpdate(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, targets):
        # logic based on https://jts.seagate.com/browse/EOS-6611?focusedCommentId=1833451&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-1833451  # noqa: E501

        def _update_component(component):
            state_name = "components.{}.update".format(component)
            try:
                logger.info(
                    "Updating {} on {}".format(component, targets)
                )
                StatesApplier.apply([state_name], targets)
            except Exception:
                logger.exception(
                    "Failed to update {} on {}"
                    .format(component, targets)
                )
                raise

        # TODO:
        #   - create a state instead
        #   - what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        # TODO IMPROVE minions might be stopped here in case of rollback,
        #      options: set up temp ssh config and rollback yum + minion config
        #      via ssh as a fallback
        rollback_ctx = None
        try:
            # ensure update repos are configured
            StatesApplier.apply(
                ['components.misc_pkgs.eosupdate.repo'], targets
            )

            with YumRollbackManager(
                targets, multiple_targets_ok=True
            ) as rollback_ctx:
                try:
                    cluster_maintenance_enable()
                except Exception as exc:
                    raise ClusterMaintenanceEnableError(exc) from exc

                try:
                    # provisioner update
                    _update_component('provisioner')
                    config_salt_master()
                    config_salt_minions()

                    # update other components
                    for component in (
                        'eoscore', 's3server', 'hare', 'sspl', 'csm'
                    ):
                        _update_component(component)
                except Exception as exc:
                    raise SWStackUpdateError(exc) from exc

                # SW stack now in "updated" state
                try:
                    cluster_maintenance_disable()
                except Exception as exc:
                    raise ClusterMaintenanceDisableError(exc) from exc

        except Exception as update_exc:
            # TODO TEST
            logger.exception('SW Update failed')

            rollback_error = (
                None if rollback_ctx is None else rollback_ctx.rollback_error
            )
            final_error_t = SWUpdateError

            if rollback_error:
                # unrecoverable state: SW stack is in intermediate state,
                # no sense to start the cluster ??? verify TODO IMPROVE
                logger.error(
                    'Yum Rollback failed: {}'
                    .format(rollback_ctx.rollback_error)
                )
                final_error_t = SWUpdateFatalError
            else:
                # yum changes reverted now
                if isinstance(update_exc, ClusterMaintenanceEnableError):
                    # failed to activate maintenance, cluster will likely
                    # fail to start - fail gracefully:  disable
                    # maintenance in the background
                    cluster_maintenance_disable(background=True)
                elif isinstance(
                    update_exc,
                    (SWStackUpdateError, ClusterMaintenanceDisableError)
                ):
                    # rollback provisioner related configuration
                    try:
                        # ensure previous configuration for salt
                        ensure_salt_master_is_running()
                        config_salt_master()
                        config_salt_minions()
                        StatesApplier.apply(
                            ["components.provisioner.config"], targets
                        )
                    except Exception as exc:
                        # unrecoverable state: SW stack is in intermediate
                        # state, no sense to start the cluster
                        logger.exception(
                            'Failed to restore SaltStack configuration'
                        )
                        rollback_error = exc
                        final_error_t = SWUpdateFatalError
                    else:
                        # SW stack now in "initial" state
                        try:
                            cluster_maintenance_disable()
                        except Exception as exc:
                            # unrecoverable state: SW stack is in initial
                            # state but cluster failed to start
                            logger.exception(
                                'Failed to start cluster after rollback'
                            )
                            rollback_error = exc
                            final_error_t = SWUpdateFatalError
                        # update failed but node is in initial state
                        # and looks functional
                else:
                    # TODO TEST unit for that case
                    pass  # it might be update repo set issue

            # TODO IMPROVE
            raise final_error_t(
                update_exc, rollback_error=rollback_error
            ) from update_exc


# TODO TEST
@attr.s(auto_attribs=True)
class FWUpdate(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsFWUpdate

    def run(self, source, dry_run=False):
        source = Path(source).resolve()

        if not source.is_file():
            raise ValueError('{} is not a file'.format(source))

        script = (
            PRVSNR_FILEROOTS_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )
        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = Param(
            'ip', 'storage_enclosure.sls',
            controller_pi_path / 'primary_mc/ip'
        )
        user = Param(
            'user', 'storage_enclosure.sls',
            controller_pi_path / 'user'
        )
        passwd = Param(
            'passwd', 'storage_enclosure.sls',
            controller_pi_path / 'secret'
        )
        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.pi_key)
                )

        if dry_run:
            return

        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name=(
                    "{script} host -h {ip} -u {user} -p {passwd} "
                    "--update-fw {source}"
                    .format(
                        script=script,
                        ip=pillar[ip],
                        user=pillar[user],
                        passwd=pillar[passwd],
                        source=source
                    )
                )
            )
        )


@attr.s(auto_attribs=True)
class GetResult(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsGetResult

    def run(self, cmd_id: str):
        return SaltJobsRunner.prvsnr_job_result(cmd_id)


# TODO TEST
@attr.s(auto_attribs=True)
class GetClusterId(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    def run(self):
        return list(function_run(
            'grains.get',
            fun_args=['cluster_id']
        ).values())[0]


# TODO TEST
@attr.s(auto_attribs=True)
class GetNodeId(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self, targets):
        return function_run(
            'grains.get',
            fun_args=['node_id'],
            targets=targets
        )

# TODO TEST
# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class SetSSLCerts(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSSLCerts

    def run(self, source, restart=False, dry_run=False):

        source = Path(source).resolve()
        dest = PRVSNR_USER_FILES_SSL_CERTS_FILE
        time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        state_name = "components.misc_pkgs.ssl_certs"

        if not source.is_file():
            raise ValueError('{} is not a file'.format(source))

        if dry_run:
            return

        try:
            #move cluster to maintenance mode
            try:
                cluster_maintenance_enable()
                logger.info('Cluster maintenance mode enabled')
            except Exception as exc:
                raise ClusterMaintenanceEnableError(exc) from exc
       
            copy_to_file_roots(source, dest) 
            
            try:
                #backup old ssl certs to provisioner user files
                backup_file_name = copy_to_file_roots(SSL_CERTS_FILE,
                    dest.parent / '{}_{}'.format(time_stamp, dest.name))
                StatesApplier.apply([state_name])
                logger.info('SSL Certs Updated')
            except Exception as exc:
                logger.exception(
                    "Failed to apply certs")
                raise SSLCertsUpdateError(exc) from exc
            
            #disable cluster maintenance mode
            try:
                cluster_maintenance_disable()
                logger.info('Cluster recovered from maintenance mode')
            except Exception as exc:
                raise ClusterMaintenanceDisableError(exc) from exc
            
        except Exception as ssl_exc:
            logger.exception('SSL Certs Updation Failed')
            rollback_exc = None
            if isinstance(ssl_exc, ClusterMaintenanceEnableError):
                cluster_maintenance_disable(background=True)

            elif isinstance(ssl_exc,
                (SSLCertsUpdateError, ClusterMaintenanceDisableError)):
                
                logger.info('Restoring old SSL cert ')
                # restores old cert  
                copy_to_file_roots(backup_file_name, dest) 

                try:
                    StatesApplier.apply([state_name])
                except Exception as exc:
                    logger.exception(
                        "Failed to apply backedup certs")
                    rollback_exc = exc
                else:
                    try:
                        cluster_maintenance_disable()
                    except Exception as exc:
                        logger.exception(
                            "Failed to recover Cluster after rollback")
                        rollback_exc = exc
            else: 
                logger.warning('Unexpected error: {!r}'.format(ssl_exc))

            raise SSLCertsUpdateError(ssl_exc, rollback_exc = rollback_exc)


# TODO TEST
@attr.s(auto_attribs=True)
class RebootServer(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self, targets):
        return function_run(
            'system.reboot',
            targets=targets
        )


# TODO IMPROVE dry-run mode
@attr.s(auto_attribs=True)
class RebootController(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsController

    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, target_ctrl: str = CONTROLLER_BOTH):

        script = (
            PRVSNR_FILEROOTS_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )
        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = Param(
            'ip', 'storage_enclosure.sls',
            controller_pi_path / 'primary_mc/ip'
        )
        user = Param(
            'user', 'storage_enclosure.sls',
            controller_pi_path / 'user'
        )
        passwd = Param(
            'passwd', 'storage_enclosure.sls',
            controller_pi_path / 'secret'
        )
        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.pi_key)
                )

        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name=(
                    "{script} host -h {ip} -u {user} -p {passwd} "
                    "--restart-ctrl {target_ctrl}"
                    .format(
                        script=script,
                        ip=pillar[ip],
                        user=pillar[user],
                        passwd=pillar[passwd],
                        target_ctrl=target_ctrl
                    )
                )
            )
        )


# TODO IMPROVE dry-run mode
@attr.s(auto_attribs=True)
class ShutdownController(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsController

    @classmethod
    def from_spec(cls):
        return cls()

    def run(self, target_ctrl: str = CONTROLLER_BOTH):

        script = (
            PRVSNR_FILEROOTS_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )
        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = Param(
            'ip', 'storage_enclosure.sls',
            controller_pi_path / 'primary_mc/ip'
        )
        user = Param(
            'user', 'storage_enclosure.sls',
            controller_pi_path / 'user'
        )
        # TODO IMPROVE improve Param to hide secrets
        passwd = Param(
            'passwd', 'storage_enclosure.sls',
            controller_pi_path / 'secret'
        )
        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.pi_key)
                )

        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name=(
                    "{script} host -h {ip} -u {user} -p {passwd} "
                    "--shutdown-ctrl {target_ctrl}"
                    .format(
                        script=script,
                        ip=pillar[ip],
                        user=pillar[user],
                        passwd=pillar[passwd],
                        target_ctrl=target_ctrl
                    )
                )
            )
        )


@attr.s(auto_attribs=True)
class ConfigureEOS(CommandParserFillerMixin):
    params_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureEOS

    def run(
        self, component, source=None, show=False, reset=False
    ):
        if source and not (show or reset):
            pillar = load_yaml(source)
        else:
            pillar = None

        res = PillarUpdater().component_pillar(
            component, show=show, reset=reset, pillar=pillar
        )

        if show:
            print(dump_yaml_str(res))


commands = {}
for command_name, spec in api_spec.items():
    spec = deepcopy(api_spec[command_name])  # TODO
    command = getattr(_mod, spec.pop('type'))
    commands[command_name] = command.from_spec(**spec)
