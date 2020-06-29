import sys
import attr
from typing import List, Dict, Type, Union, Optional, Iterable
from copy import deepcopy
import logging
import uuid
from pathlib import Path

from .errors import (
    ProvisionerError,
    BadPillarDataError,
    PillarSetError,
    SWUpdateError,
    SWUpdateFatalError,
    ClusterMaintenanceEnableError,
    SWStackUpdateError,
    ClusterMaintenanceDisableError,
    HAPostUpdateError,
    ClusterNotHealthyError,
    SaltCmdResultError
)
from .config import (
    ALL_MINIONS, PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR,
    PRVSNR_FILEROOTS_DIR, LOCAL_MINION,
    PRVSNR_USER_FILES_SSL_CERTS_FILE,
    PRVSNR_EOS_COMPONENTS,
    CONTROLLER_BOTH,
    SEAGATE_USER_HOME_DIR, SEAGATE_USER_FILEROOTS_DIR_TMPL
)
from .pillar import (
    KeyPath,
    PillarKey,
    PillarUpdater,
    PillarResolver
)
# TODO IMPROVE EOS-8473
from . import config, profile
from .utils import (
    load_yaml, dump_yaml,
    load_yaml_str, dump_yaml_str,
    repo_tgz, run_subprocess_cmd
)
from .api_spec import api_spec
from .ssh import keygen
from .salt import (
    StatesApplier,
    StateFunExecuter,
    State,
    YumRollbackManager,
    SaltJobsRunner, function_run,
    copy_to_file_roots,
    SaltSSHClient
)
from .hare import (
    cluster_maintenance_enable,
    cluster_maintenance_disable,
    apply_ha_post_update,
    ensure_cluster_is_healthy
)
from .salt_master import (
    config_salt_master,
    ensure_salt_master_is_running
)
from .salt_minion import config_salt_minions
from . import inputs, values

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


# TODO TEST EOS-8473
class RunArgsSetup:
    name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "A name to assign to the setup, "
                    "auto-generated if not specified"
                ),
            }
        },
        default=None
    )
    prvsnr_verion: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Provisioner version to setup",
            }
        },
        default=None
    )
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the source for provisioner repo installation",
                'choices': ['local', 'gitlab', 'gitrepo', 'rpm']
            }
        },
        default='rpm'
    )
    local_repo: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the path to local provisioner repo"
            }
        },
        default=config.PROJECT_PATH,
        converter=(lambda v: Path(str(v)))
    )
    target_build: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "Cortex integration release version relative to "
                    f"{config.CORTX_REPOS_BASE_URL}"
                ),
            }
        },
        default='integration/centos-7.7.1908/last_successful',
        converter=(lambda v: f'{config.CORTX_REPOS_BASE_URL}/{v}')
    )
    ha: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "turn on high availbility setup",
            }
        },
        default=False
    )
    salt_master: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "domain name or IP of the salt master"
            }
        },
        default=None
    )
    update: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "update initial configuration",
            }
        },
        default=False
    )


# TODO TEST EOS-8473
# TODO IMPROVE EOS-8473 converters and validators
@attr.s(auto_attribs=True)
class NodeGrains:
    fqdn: str = None
    host: str = None
    ipv4: List = attr.Factory(list)
    fqdns: List = attr.Factory(list)
    not_used: Dict = attr.Factory(dict)

    @classmethod
    def from_grains(cls, **kwargs):
        # Note. assumtion that 'not_used' doesn't appear in grains
        not_used = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k not in attr.fields_dict(cls)
        }
        return cls(**kwargs, not_used=not_used)

    @property
    def addrs(self):
        res = []
        for _attr in ('host', 'fqdn', 'fqdns', 'ipv4'):
            v = getattr(self, _attr)
            if v:
                if type(v) is list:
                    res.extend(v)
                else:  # str is expected
                    res.append(v)
        return list(set(res))


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class Node:
    minion_id: str
    host: str
    user: str = 'root'
    port: int = 22

    grains: Optional[NodeGrains] = None
    # ordered by priority
    _ping_addrs: List = attr.Factory(list)

    @classmethod
    def from_spec(cls, spec: str) -> 'Node':
        kwargs = {}

        parts = spec.split(':')
        kwargs['minion_id'] = parts[0]
        hostspec = parts[1]

        try:
            kwargs['port'] = parts[2]
        except IndexError:
            pass

        parts = hostspec.split('@')
        try:
            kwargs['user'] = parts[0]
            kwargs['host'] = parts[1]
        except IndexError:
            del kwargs['user']
            kwargs['host'] = parts[0]

        return cls(**kwargs)

    def __str__(self):
        return (
            '{}:{}@{}:{}'
            .format(
                self.minion_id,
                self.user,
                self.host,
                self.port
            )
        )

    @property
    def addrs(self):
        return list(set([self.host] + self.grains.addrs))

    @property
    def ping_addrs(self):
        return self._ping_addrs

    @ping_addrs.setter
    def ping_addrs(self, addrs: Iterable):
        # TODO IMPROVE EOS-8473 more effective way to order
        #      w.g. use dict (it remembers the order) and set intersection
        priorities = [
            self.grains.fqdn
        ] + self.grains.fqdns + [
            self.host,
            self.grains.host
        ] + self.grains.ipv4

        self._ping_addrs[:] = []
        for addr in priorities:
            if addr in addrs and (addr not in self._ping_addrs):
                self._ping_addrs.append(addr)

        for addr in addrs:
            if addr not in self._ping_addrs:
                self._ping_addrs.append(addr)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class RunArgsSetupProvisionerBase:
    name: str = RunArgsSetup.name
    source: str = RunArgsSetup.source
    prvsnr_verion: str = RunArgsSetup.prvsnr_verion
    local_repo: str = RunArgsSetup.local_repo
    target_build: str = RunArgsSetup.target_build
    salt_master: str = RunArgsSetup.salt_master
    update: bool = RunArgsSetup.update


@attr.s(auto_attribs=True)
class RunArgsSetupProvisionerGeneric(RunArgsSetupProvisionerBase):
    ha: bool = RunArgsSetup.ha
    nodes: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "cluster node specification, "
                    "format: [id:][user@]hostname[:port]"
                ),
                'nargs': '*'
            }
        },
        default=None,
        converter=(
            lambda specs: [
                (s if isinstance(s, Node) else Node.from_spec(s))
                for s in specs
            ]
        )
    )

    @property
    def primary(self):
        return self.nodes[0]

    @property
    def secondaries(self):
        return self.nodes[1:]


@attr.s(auto_attribs=True)
class RunArgsSetupSinglenode(RunArgsSetupProvisionerBase):
    srvnode1: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "srvnode-1 host specification",
                'metavar': '[user@]hostname[:port]'
            }
        },
        default=config.LOCALHOST_IP,
        converter=(lambda s: Node.from_spec(f"srvnode-1:{s}"))
    )
    salt_master: str = attr.ib(init=False,  default=None)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class RunArgsSetupCluster(RunArgsSetupSinglenode):
    ha: bool = RunArgsSetup.ha
    srvnode2: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "srvnode-2 host specification",
                'metavar': '[user@]hostname[:port]'
            }
        },
        default='srvnode-2',
        converter=(lambda s: Node.from_spec(f"srvnode-2:{s}"))
    )

    """
    @srvnode2.validator
    def _check_srvnode2(self, attribute, value):
        parts = value.split('@')
        if len(parts) > 2 or len(parts) == 0 or [p for p in parts if not p]:
            raise ValueError(
                f"{attribute.name} should be a valid hostspec [user@]host, "
                f"provided '{value}'"
            )
    """


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


@attr.s(auto_attribs=True)
class RunArgsUser:
    uname: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "name of the user"
            }
        }
    )
    passwd: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "password for the user"
            }
        }
    )
    targets: str = RunArgs.targets


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
    input_type: Type[inputs.PillarKeysList] = inputs.PillarKeysList

    @classmethod
    def from_spec(
        cls, input_type: str = 'PillarKeysList'
    ):
        return cls(input_type=getattr(inputs, input_type))

    def run(self, *args, targets: str = ALL_MINIONS, **kwargs):
        pi_keys = self.input_type.from_args(*args, **kwargs)
        pillar_resolver = PillarResolver(targets=targets)

        if len(pi_keys):
            res_raw = pillar_resolver.get(pi_keys)
            res = {}
            for minion_id, data in res_raw.items():
                res[minion_id] = {str(pk): v for pk, v in data.items()}
            return res
        else:
            return pillar_resolver.pillar


@attr.s(auto_attribs=True)
class PillarSet(CommandParserFillerMixin):
    # TODO at least either pre or post should be defined
    input_type: Type[inputs.PillarInputBase] = inputs.PillarInputBase

    _run_args_type = RunArgsUpdate

    # TODO input class type
    @classmethod
    def from_spec(
        cls, input_type: str = 'PillarInputBase'
    ):
        return cls(
            input_type=getattr(inputs, input_type)
        )

    # TODO
    # - class for pillar file
    # - caching (load once)
    def run(self, *args, targets=ALL_MINIONS, dry_run=False, **kwargs):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.input_type):
            input_data = args[0]
        else:
            input_data = self.input_type.from_args(*args, **kwargs)

        # TODO dynamic validation
        if dry_run:
            return

        exc = None
        rollback_exc = None

        try:
            pillar_updater = PillarUpdater(targets)
            pillar_updater.update(input_data)

            try:
                pillar_updater.apply()
            except Exception:
                try:
                    # TODO more solid rollback:
                    #   - rollback might be not needed at all
                    #   - or needed partually
                    pillar_updater.rollback()
                    pillar_updater.apply()
                except Exception as _exc:
                    rollback_exc = _exc
                raise
        except Exception as _exc:
            exc = _exc
            logger.exception('Pillar set failed')
        finally:
            if exc:
                raise PillarSetError(
                    reason=exc, rollback_error=rollback_exc
                )


@attr.s(auto_attribs=True)
class Get(CommandParserFillerMixin):
    input_type: Type[inputs.ParamsList] = inputs.ParamsList

    # TODO input class type
    @classmethod
    def from_spec(
        cls, input_type: str = 'ParamsList'
    ):
        return cls(input_type=getattr(inputs, input_type))

    def run(self, *args, targets=ALL_MINIONS, **kwargs):
        # TODO tests
        params = self.input_type.from_args(*args, **kwargs)
        pillar_resolver = PillarResolver(targets=targets)
        res_raw = pillar_resolver.get(params)
        res = {}
        for minion_id, data in res_raw.items():
            res[minion_id] = {str(p): v for p, v in data.items()}
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
    input_type: Type[
        Union[inputs.ParamGroupInputBase, inputs.ParamDictItemInputBase]
    ]
    pre_states: List[State] = attr.Factory(list)
    post_states: List[State] = attr.Factory(list)

    _run_args_type = RunArgsUpdate

    # TODO input class type
    @classmethod
    def from_spec(
        cls, input_type: str, states: Dict
    ):
        return cls(
            input_type=getattr(inputs, input_type),
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
        if len(args) == 1 and isinstance(args[0], self.input_type):
            params = args[0]
        else:
            params = self.input_type.from_args(*args, **kwargs)

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
    input_type: Type[inputs.EOSUpdateRepo] = inputs.EOSUpdateRepo

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


# TODO IMPROVE EOS-8940 move to separate module
def _ensure_update_repos_configuration(targets=ALL_MINIONS):
    logger.info("Ensure update repos are configured")
    StatesApplier.apply(
        ['components.misc_pkgs.eosupdate.repo'], targets
    )


def _pre_yum_rollback(
    rollback_ctx, exc_type, exc_value, exc_traceback
):
    if isinstance(
        exc_value, (HAPostUpdateError, ClusterNotHealthyError)
    ):
        try:
            logger.info(
                "Enable cluster maintenance mode before rollback"
            )
            cluster_maintenance_enable()
        except Exception as exc:
            raise ClusterMaintenanceEnableError(exc) from exc


def _update_component(component, targets=ALL_MINIONS):
    state_name = "components.{}.update".format(component)
    try:
        logger.info(
            "Updating {} on {}".format(component, targets)
        )
        StatesApplier.apply([state_name], targets)
    except Exception:
        logger.exception(
            "Failed to update {} on {}".format(component, targets)
        )
        raise


def _apply_provisioner_config(targets=ALL_MINIONS):
    logger.info(f"Applying Provisioner config logic on {targets}")
    StatesApplier.apply(["components.provisioner.config"], targets)


# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class EOSUpdate(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, targets):
        # logic based on https://jts.seagate.com/browse/EOS-6611?focusedCommentId=1833451&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-1833451  # noqa: E501

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
            ensure_cluster_is_healthy()

            _ensure_update_repos_configuration(targets)

            with YumRollbackManager(
                targets,
                multiple_targets_ok=True,
                pre_rollback_cb=_pre_yum_rollback
            ) as rollback_ctx:
                # enable "smart maintenance" mode
                try:
                    cluster_maintenance_enable()
                except Exception as exc:
                    raise ClusterMaintenanceEnableError(exc) from exc

                # update SW stack packages and configuration
                try:
                    _update_component('provisioner', targets)

                    config_salt_master()

                    config_salt_minions()

                    for component in (
                        'cortx-motr', 's3server', 'hare', 'sspl', 'csm'
                    ):
                        _update_component(component, targets)
                except Exception as exc:
                    raise SWStackUpdateError(exc) from exc

                # SW stack now in "updated" state
                # disable "smart maintenance" mode
                try:
                    cluster_maintenance_disable()
                except Exception as exc:
                    raise ClusterMaintenanceDisableError(exc) from exc

                # call Hare to update cluster configuration
                try:
                    apply_ha_post_update(targets)
                except Exception as exc:
                    raise HAPostUpdateError(exc) from exc

                try:
                    ensure_cluster_is_healthy()
                except Exception as exc:
                    raise ClusterNotHealthyError(exc) from exc

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
                    'Rollback failed: {}'
                    .format(rollback_ctx.rollback_error)
                )
                final_error_t = SWUpdateFatalError
            elif rollback_ctx is not None:
                # yum packages are in initial state here

                if isinstance(update_exc, ClusterMaintenanceEnableError):
                    # failed to activate maintenance, cluster will likely
                    # fail to start - fail gracefully:  disable
                    # maintenance in the background
                    cluster_maintenance_disable(background=True)
                elif isinstance(
                    # cluster is stopped here
                    update_exc,
                    (
                        SWStackUpdateError,
                        ClusterMaintenanceDisableError,
                        HAPostUpdateError,
                        ClusterNotHealthyError
                    )
                ):
                    # rollback provisioner related configuration
                    try:
                        ensure_salt_master_is_running()

                        config_salt_master()

                        config_salt_minions()

                        _apply_provisioner_config(targets)

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

                            apply_ha_post_update(targets)

                            ensure_cluster_is_healthy()
                        except Exception as exc:
                            # unrecoverable state: SW stack is in initial
                            # state but cluster failed to start
                            logger.exception(
                                'Failed to recover cluster after rollback'
                            )
                            rollback_error = exc
                            final_error_t = SWUpdateFatalError

                        # update failed but node is in initial state
                        # and looks functional
                else:
                    # TODO TEST unit for that case
                    logger.warning(
                        'Unexpected case: update exc {!r}'.format(update_exc)
                    )

            # TODO IMPROVE
            raise final_error_t(
                update_exc, rollback_error=rollback_error
            ) from update_exc


# TODO TEST
@attr.s(auto_attribs=True)
class FWUpdate(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
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
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        passwd = PillarKey(controller_pi_path / 'secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
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
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsGetResult

    def run(self, cmd_id: str):
        return SaltJobsRunner.prvsnr_job_result(cmd_id)


# TODO TEST
@attr.s(auto_attribs=True)
class GetClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    def run(self):
        return list(function_run(
            'grains.get',
            fun_args=['cluster_id']
        ).values())[0]


# TODO TEST
@attr.s(auto_attribs=True)
class GetNodeId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
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
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSSLCerts

    def run(self, source, restart=False, dry_run=False):

        source = Path(source).resolve()

        if not source.is_file():
            raise ValueError('{} is not a file'.format(source))

        if dry_run:
            return

        try:
            cluster_maintenance_enable()
        except Exception as exc:
            raise ClusterMaintenanceEnableError(exc) from exc

        # TODO create backup and add timestamp to backups
        copy_to_file_roots(source, PRVSNR_USER_FILES_SSL_CERTS_FILE)

        try:
            StatesApplier.apply(["components.misc_pkgs.ssl_certs"])
        except Exception:
            logger.exception(
                "Failed to apply certs"
            )
            raise

        try:
            cluster_maintenance_disable()
        except Exception as exc:
            raise ClusterMaintenanceDisableError(exc) from exc


# TODO TEST
@attr.s(auto_attribs=True)
class RebootServer(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self, targets):
        return function_run(
            'system.reboot',
            targets=targets
        )


# TODO IMPROVE dry-run mode
@attr.s(auto_attribs=True)
class RebootController(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
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
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        passwd = PillarKey(controller_pi_path / 'secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
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
    input_type: Type[inputs.NoParams] = inputs.NoParams
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
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        passwd = PillarKey(controller_pi_path / 'secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
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
    input_type: Type[inputs.NoParams] = inputs.NoParams
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


@attr.s(auto_attribs=True)
class CreateUser(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsUser

    def run(self, uname, passwd, targets: str = ALL_MINIONS):

        if not SEAGATE_USER_HOME_DIR.exists():
            raise ValueError('/opt/seagate/users directory missing')

        home_dir = SEAGATE_USER_HOME_DIR / uname
        ssh_dir = home_dir / '.ssh'

        user_fileroots_dir = Path(
            PRVSNR_FILEROOTS_DIR /
            SEAGATE_USER_FILEROOTS_DIR_TMPL.format(uname=uname)
        )

        keyfile = user_fileroots_dir / f'id_rsa_{uname}'
        keyfile_pub = keyfile.with_name(f'{keyfile.name}.pub')

        nodes = PillarKey('cluster/node_list')

        nodelist_pillar = PillarResolver(LOCAL_MINION).get([nodes])
        nodelist_pillar = next(iter(nodelist_pillar.values()))

        if (not nodelist_pillar[nodes] or
                nodelist_pillar[nodes] is values.MISSED):
            raise BadPillarDataError(
                'value for {} is not specified'.format(nodes.pi_key)
            )

        def _prepare_user_fileroots_dir():
            StateFunExecuter.execute(
                'file.directory',
                fun_kwargs=dict(
                    name=str(user_fileroots_dir),
                    makedirs=True
                )
            )

        def _generate_ssh_keys():
            StateFunExecuter.execute(
                'cmd.run',
                fun_kwargs=dict(
                    name=(
                        f"ssh-keygen -f {keyfile} "
                        "-q -C '' -N '' "
                        "-t rsa -b 4096 <<< y"
                    )
                )
            )
            StateFunExecuter.execute(
                'ssh_auth.present',
                fun_kwargs=dict(
                    # name param is mandetory and expects ssh key
                    # but ssh key is passed as source file hence name=None
                    name=None,
                    user=uname,
                    source=str(keyfile_pub),
                    config=str(user_fileroots_dir / 'authorized_keys')
                )
            )

        def _generate_ssh_config():
            for node in nodelist_pillar[nodes]:
                hostname = PillarKey(
                    'cluster/'+node+'/hostname'
                )

                hostname_pillar = PillarResolver(LOCAL_MINION).get([hostname])
                hostname_pillar = next(iter(hostname_pillar.values()))

                if (not hostname_pillar[hostname] or
                        hostname_pillar[hostname] is values.MISSED):
                    raise BadPillarDataError(
                        'value for {} is not specified'.format(hostname.pi_key)
                    )

                ssh_config = f'''Host {node} {hostname_pillar[hostname]}
    Hostname {hostname_pillar[hostname]}
    User {uname}
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile {ssh_dir}/{keyfile.name}
    IdentitiesOnly yes
    LogLevel ERROR
    BatchMode yes'''

                StateFunExecuter.execute(
                    'file.append',
                    fun_kwargs=dict(
                        name=str(user_fileroots_dir / 'config'),
                        text=ssh_config
                    )
                )

        def _copy_minion_nodes():
            StateFunExecuter.execute(
                'file.recurse',
                fun_kwargs=dict(
                    name=str(ssh_dir),
                    source=str(
                        'salt://' +
                        SEAGATE_USER_FILEROOTS_DIR_TMPL.format(uname=uname)
                    ),
                    user=uname,
                    group=uname,
                    file_mode='600',
                    dir_mode='700'
                ),
                targets=targets
            )

        def _passwordless_ssh():
            _prepare_user_fileroots_dir()
            _generate_ssh_keys()
            _generate_ssh_config()
            _copy_minion_nodes()

        StateFunExecuter.execute(
            'user.present',
            fun_kwargs=dict(
                name=uname,
                password=passwd,
                hash_password=True,
                home=str(home_dir),
                groups=['wheel']
            ),
            targets=targets
        )
        logger.info(
            'Setting up passowrdless ssh for {uname} user on both the nodes'
            .format(
                uname=uname
            )
        )
        _passwordless_ssh()


@attr.s(auto_attribs=True)
class SetupCtx:
    run_args: RunArgsSetupProvisionerGeneric
    profile_paths: Dict
    ssh_client: SaltSSHClient


# TODO TEST EOS-8473
# TODO DOC highlights
#   - multiple setups support
#   - idempotence: might be run multiple times,
#       re-tries much faster (2-3 times)
#   - multi-master initial support:
#       - list of masters is auto-generated
#         (each to each reachability is checked)
#   - parallel setup of multiple nodes
#   - paswordless ssh setup to nodes is supported
@attr.s(auto_attribs=True)
class SetupProvisioner(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSetupProvisionerGeneric

    def _resolve_grains(self, nodes: List[Node], ssh_client):
        salt_ret = ssh_client.run('grains.items')
        for node in nodes:
            # assume that list of nodes matches the result
            # TODO IMPROVE EOS-8473 better parser for grains return
            node.grains = NodeGrains.from_grains(
                **salt_ret[node.minion_id]['return']
            )

    def _prepare_roster(self, nodes: List[Node], profile_paths):
        roster = {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(profile_paths['setup_key_file'])
            } for node in nodes
        }
        dump_yaml(profile_paths['salt_roster_file'], roster)

    def _create_ssh_client(self, c_path, roster_file):
        # TODO IMPROVE EOS-8473 optional support for known hosts
        ssh_options = [
            'UserKnownHostsFile=/dev/null',
            'StrictHostKeyChecking=no'
        ]
        return SaltSSHClient(
            c_path=c_path,
            roster_file=roster_file,
            ssh_options=ssh_options
        )

    def _resolve_connections(self, nodes: List[Node], ssh_client):
        addrs = {}

        for node in nodes:
            addrs[node.minion_id] = set(
                [
                    v for v in node.addrs
                    if v not in (config.LOCALHOST_IP, config.LOCALHOST_DOMAIN)
                ]
            )

        for node in nodes:
            pings = set()
            candidates = set(addrs[node.minion_id])
            for _node in nodes:
                if _node is not node:
                    candidates -= addrs[_node.minion_id]

            targets = ','.join(
                [_node.minion_id for _node in nodes if _node is not node]
            )

            for addr in candidates:
                try:
                    ssh_client.cmd_run(
                        f"ping -c 1 -W 1 {addr}", targets=targets
                    )
                except SaltCmdResultError as exc:
                    logger.debug(
                        f"Possible address '{addr}' "
                        f"of {node.minion_id} is not reachable "
                        f"from some nodes: {exc}"
                    )
                else:
                    pings.add(addr)

            if pings:
                logger.info(
                    f"{node.minion_id} is reachable "
                    f"from other nodes by: {pings}"
                )
            else:
                raise ProvisionerError(
                    f"{node.minion_id} is not reachable"
                    f"from other nodes by any of {candidates}"
                )

            node.ping_addrs = list(pings)

    def _prepare_salt_masters(self, run_args):
        res = {}

        # TODO IMPROVE EOS-8473 hardcoded
        if len(run_args.nodes) == 1:
            res[run_args.nodes[0].minion_id] = [
                run_args.salt_master if run_args.salt_master
                else config.LOCALHOST_IP
            ]
            return res

        if not run_args.salt_master:
            master_nodes = (
                run_args.nodes if run_args.ha else [run_args.primary]
            )
            masters = {
                node.minion_id: node.ping_addrs[0]
                for node in master_nodes
            }
            for node in run_args.nodes:
                res[node.minion_id] = []
                for _node in run_args.nodes:
                    # not any node may be a master
                    if _node.minion_id in masters:
                        res[node.minion_id].append(
                            config.LOCALHOST_IP if _node is node
                            else masters[_node.minion_id]
                        )
        else:
            res = {
                node.minion_id: [run_args.salt_master]
                for node in run_args.nodes
            }

        return res

    def _prepare_local_repo(self, run_args, repo_dir: Path):
        # ensure parent dirs exists in profile file root
        run_subprocess_cmd(['rm', '-rf', str(repo_dir)])
        repo_dir.mkdir(parents=True, exist_ok=True)

        # (locally) prepare tgz
        repo_tgz_path = repo_dir.parent / 'repo.tgz'
        repo_tgz(
            repo_tgz_path,
            project_path=run_args.local_repo,
            version=run_args.prvsnr_verion,
            include_dirs=['pillar', 'srv', 'files', 'api']
        )

        # extract archive locally
        run_subprocess_cmd(
            ['tar', '-zxf', str(repo_tgz_path), '-C', str(repo_dir)]
        )

        # TODO IMPROVE use salt caller and file-managed instead
        # set proper cluster.sls from template
        cluster_sls_sample_path = (
            repo_dir / 'pillar/components/samples/ees.cluster.sls'
        )
        cluster_sls_path = repo_dir / 'pillar/components/cluster.sls'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(cluster_sls_sample_path),
                str(cluster_sls_path)
            ]
        )

    def _prepare_salt_config(self, run_args, ssh_client, profile_paths):
        minions_dir = (
            profile_paths['salt_fileroot_dir'] / "provisioner/files/minions"
        )
        all_minions_dir = minions_dir / 'all'
        master_pki_dir = (
            profile_paths['salt_fileroot_dir'] / "provisioner/files/master/pki"
        )
        pillar_all_dir = profile_paths['salt_pillar_dir'] / 'groups/all'

        #   ensure parent dirs exists in profile file root
        for path in (all_minions_dir, master_pki_dir, pillar_all_dir):
            path.mkdir(parents=True, exist_ok=True)

        priv_key_path = all_minions_dir / 'id_rsa_prvsnr'
        pub_key_path = all_minions_dir / 'id_rsa_prvsnr.pub'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile_paths['setup_key_file']),
                str(priv_key_path)
            ]
        )
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile_paths['setup_key_pub_file']),
                str(pub_key_path)
            ]
        )

        conns_pillar_path = pillar_all_dir / 'connections.sls'
        if not conns_pillar_path.exists():
            self._resolve_connections(run_args.nodes, ssh_client)
            conns = {
                node.minion_id: node.ping_addrs for node in run_args.nodes
            }
            dump_yaml(conns_pillar_path,  dict(connections=conns))
        else:
            conns = load_yaml(conns_pillar_path)['connections']
            for node in run_args.nodes:
                node.ping_addrs = conns[node.minion_id]

        # IMRPOVE EOS-8473 it's not a salt minion config thing
        specs_pillar_path = pillar_all_dir / 'node_specs.sls'
        if not specs_pillar_path.exists():
            specs = {
                node.minion_id: {
                    'user': 'root',
                    'host': node.ping_addrs[0],
                    'port': node.port
                }
                for node in run_args.nodes
            }
            dump_yaml(specs_pillar_path,  dict(node_specs=specs))

        # resolve salt masters
        # TODO IMPROVE EOS-8473 option to re-build masters
        masters_pillar_path = pillar_all_dir / 'masters.sls'
        if not masters_pillar_path.exists():
            masters = self._prepare_salt_masters(run_args)
            logger.info(
                f"salt masters would be set as follows: {masters}"
            )
            dump_yaml(masters_pillar_path,  dict(masters=masters))

        cluster_id_path = all_minions_dir / 'cluster_id'
        if not cluster_id_path.exists():
            cluster_uuid = uuid.uuid4()
            dump_yaml(cluster_id_path, dict(cluster_id=str(cluster_uuid)))

        #   TODO IMPROVE EOS-8473 use salt caller and file-managed instead
        #   (locally) prepare minion config
        #   FIXME not valid for non 'local' source
        minion_cfg_sample_path = (
            run_args.local_repo /
            'srv/components/provisioner/salt_minion/files/minion'
        )
        minion_cfg_path = all_minions_dir / 'minion'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(minion_cfg_sample_path),
                str(minion_cfg_path)
            ]
        )
        run_subprocess_cmd(
            [
                'sed', '-i',
                "s/^master: .*/master: {{ pillar['masters'][grains['id']] }}/g",  # noqa: E501
                str(minion_cfg_path)
            ]
        )

        for node in run_args.nodes:
            node_dir = minions_dir / f"{node.minion_id}"
            node_pki_dir = node_dir / 'pki'

            #   ensure parent dirs exists in profile file root
            node_pki_dir.mkdir(parents=True, exist_ok=True)

            #   TODO IMPROVE use salt caller and file-managed instead
            #   (locally) prepare minion grains
            #   FIXME not valid for non 'local' source
            minion_grains_sample_path = (
                run_args.local_repo / (
                    "srv/components/provisioner/salt_minion/files/grains.{}"
                    .format(
                        'primary' if node is run_args.primary else 'secondary'
                    )
                )
            )
            minion_grains_path = node_dir / 'grains'
            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(minion_grains_sample_path),
                    str(minion_grains_path)
                ]
            )

            #   TODO IMPROVE use salt caller and file-managed instead
            #   (locally) prepare minion node_id
            minion_nodeid_path = node_dir / 'node_id'
            if not minion_nodeid_path.exists():
                node_uuid = uuid.uuid4()
                dump_yaml(minion_nodeid_path, dict(node_id=str(node_uuid)))

            # TODO IMPROVE EOS-8473 consider to move to mine data
            # (locally) prepare hostname info
            minion_hostname_status_path = node_dir / 'hostname_status'
            if not minion_hostname_status_path.exists():
                res = ssh_client.cmd_run(
                    "hostnamectl status  | sed 's/^ *//g'",
                    fun_kwargs=dict(python_shell=True),
                    targets=node.minion_id
                )
                # Note. output here is similar to yaml format
                # ensure that it is yaml parseable
                status = load_yaml_str(res[node.minion_id])
                dump_yaml(
                    minion_hostname_status_path,
                    dict(hostname_status=status)
                )

            #   preseed minion keys
            node_key_pem_tmp = node_pki_dir / f'{node.minion_id}.pem'
            node_key_pub_tmp = node_pki_dir / f'{node.minion_id}.pub'
            node_key_pem = node_pki_dir / 'minion.pem'
            node_key_pub = node_pki_dir / 'minion.pub'

            if not (node_key_pem.exists() and node_key_pub.exists()):
                run_subprocess_cmd(
                    [
                        'salt-key',
                        '--gen-keys', node.minion_id,
                        '--gen-keys-dir', str(node_pki_dir)
                    ]
                )
                node_key_pem_tmp.rename(node_key_pem)
                node_key_pub_tmp.rename(node_key_pub)

            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(node_key_pub),
                    str(master_pki_dir / node.minion_id)
                ]
            )

    def run(self, **kwargs):
        # TODO update install repos logic (salt repo changes)
        # TODO firewall make more salt oriented
        # TODO sources: gitlab | gitrepo | rpm
        # TODO get latest tags for gitlab source

        # validation
        # TODO IMPROVE EOS-8473 make generic logic
        run_args = RunArgsSetupProvisionerGeneric(**kwargs)

        # TODO IMPROVE EOS-8473 better configuration way
        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)

        # generate setup name
        setup_name = run_args.name
        if not setup_name:
            setup_name = '__'.join(
                [str(node) for node in run_args.nodes]
            )

        # PREPARE FILE & PILLAR ROOTS

        logger.info(f"Starting to build setup '{setup_name}'")

        paths = config.profile_paths(setup_name=setup_name)
        profile.setup(paths, clean=run_args.update)

        logger.info(f"Profile location '{paths['base_dir']}'")

        priv_key_path = paths['setup_key_file']
        if not priv_key_path.exists():
            logger.info('Generating setup keys')
            keygen(priv_key_path)
        else:
            logger.info('Generating setup keys [skipped]')

        logger.info("Generating a roster file")
        self._prepare_roster(run_args.nodes, paths)

        ssh_client = self._create_ssh_client(
            paths['salt_master_file'], paths['salt_roster_file']
        )

        setup_ctx = SetupCtx(run_args, paths, ssh_client)

        for node in run_args.nodes:
            logger.info(
                f"Ensuring '{node.minion_id}' is ready to accept commands"
            )
            ssh_client.ensure_ready([node.minion_id])

        logger.info("Resolving node grains")
        self._resolve_grains(run_args.nodes, ssh_client)

        #   TODO IMPROVE EOS-8473 hard coded
        logger.info("Preparing salt minions configuration")
        self._prepare_salt_config(run_args, ssh_client, paths)

        if run_args.source == 'local':
            logger.info("Preparing local repo for a setup")
            # TODO IMPROVE EOS-8473 validator
            if not run_args.local_repo:
                raise ValueError(f"local repo is undefined")
            # TODO IMPROVE EOS-8473 hard coded
            self._prepare_local_repo(
                run_args, paths['salt_fileroot_dir'] / 'provisioner/files/repo'
            )

        # Note. salt may fail to an issue with not yet cahed sources:
        # "Recurse failed: none of the specified sources were found"
        # a workaround mentioned in https://github.com/saltstack/salt/issues/32128#issuecomment-207044948  # noqa: E501
        run_subprocess_cmd(
            [
                'rm', '-rf',
                str(paths['salt_cache_dir'] / 'file_lists/roots/*')
            ]
        )

        # APPLY CONFIGURATION

        logger.info("Setting up paswordless ssh")
        ssh_client.state_apply('ssh')

        logger.info("Checking paswordless ssh")
        ssh_client.state_apply('ssh.check')

        logger.info("Installing Cortx yum repositories")
        ssh_client.state_apply('cortx_repos')

        logger.info("Configuring the firewall")
        ssh_client.state_apply('firewall')

        logger.info("Installing SaltStack")
        ssh_client.state_apply('saltstack')

        if run_args.source == 'local':
            logger.info("Installing provisioner from a local source")
            ssh_client.state_apply('provisioner.local')
        else:
            raise NotImplementedError(
                f"{run_args.source} provisioner source is not supported yet"
            )

        #   CONFIGURE SALT
        logger.info("Configuring salt minions")
        res = ssh_client.state_apply('provisioner.configure_salt_minion')

        updated_keys = []
        # TODO IMPROVE EOS-8473
        minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
        for node_id, _res in res.items():
            if _res[minion_pki_state_id]['changes']:
                updated_keys.append(node_id)

        # TODO DOC how to pass inline pillar
        logger.info("Configuring salt master")
        ssh_client.state_apply(
            'provisioner.configure_salt_master',
            targets=run_args.primary.minion_id,
            fun_kwargs={
                'pillar': {
                    'updated_keys': updated_keys
                }
            }
        )

        # FIXME EOS-8473 not necessary for rpm setup
        logger.info("Installing provisioner API")
        ssh_client.state_apply('provisioner.api_install')

        logger.info("Starting salt minions")
        ssh_client.state_apply('provisioner.start_salt_minion')

        # TODO IMPROVE EOS-8473
        logger.info("Ensuring salt minions are ready")
        nodes_ids = [node.minion_id for node in run_args.nodes]
        ssh_client.cmd_run(
            f"python3 -c \"from provisioner import salt_minion; salt_minion.ensure_salt_minions_are_ready({nodes_ids})\"",  # noqa: E501
            targets=run_args.primary.minion_id
        )

        # TODO IMPROVE EOS-8473 FROM THAT POINT REMOTE SALT SYSTEM IS FULLY
        #      CONFIGURED AND MIGHT BE USED INSTED OF SALT-SSH BASED CONTROL

        logger.info("Configuring provisioner logging")
        for state in [
            'components.system.prepare',
            'components.provisioner.config'
        ]:
            ssh_client.cmd_run(
                f"salt-call state.apply {state}",
                targets=run_args.primary.minion_id
            )

        logger.info("Updating BMC IPs")
        ssh_client.cmd_run(f"salt-call state.apply components.misc_pkgs.ipmi")

        logger.info("Updating target build pillar")
        ssh_client.cmd_run(
            (
                'provisioner pillar_set --fpath release.sls '
                f'eos_release/target_build \'"{run_args.target_build}"\''
            ), targets=run_args.primary.minion_id
        )

        return setup_ctx


@attr.s(auto_attribs=True)
class SetupSinglenode(SetupProvisioner):
    _run_args_type = RunArgsSetupSinglenode

    def run(self, **kwargs):
        run_args = RunArgsSetupSinglenode(**kwargs)
        kwargs.pop('srvnode1')

        setup_ctx = super().run(
            ha=False, nodes=[run_args.srvnode1], **kwargs
        )

        logger.info("Updating hostname in cluster pillar")

        node = setup_ctx.run_args.nodes[0]
        setup_ctx.ssh_client.cmd_run(
            (
                'provisioner pillar_set '
                f'cluster/{node.minion_id}/hostname '
                f'\'"{node.grains.fqdn}"\''
            ), targets=setup_ctx.run_args.primary.minion_id
        )

        logger.info("Done")


@attr.s(auto_attribs=True)
class SetupCluster(SetupProvisioner):
    _run_args_type = RunArgsSetupCluster

    def run(self, **kwargs):
        run_args = RunArgsSetupCluster(**kwargs)
        kwargs.pop('srvnode1')
        kwargs.pop('srvnode2')

        setup_ctx = super().run(
            nodes=[run_args.srvnode1, run_args.srvnode2], **kwargs
        )

        logger.info("Updating hostnames in cluster pillar")
        for node in setup_ctx.run_args.nodes:
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner pillar_set '
                    f'cluster/{node.minion_id}/hostname '
                    f'\'"{node.grains.fqdn}"\''
                ), targets=setup_ctx.run_args.primary.minion_id
            )

        logger.info("Done")


commands = {}
for command_name, spec in api_spec.items():
    spec = deepcopy(api_spec[command_name])  # TODO
    command = getattr(_mod, spec.pop('type'))
    commands[command_name] = command.from_spec(**spec)
