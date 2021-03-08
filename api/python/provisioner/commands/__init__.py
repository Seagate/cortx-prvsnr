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

import sys
from typing import List, Dict, Type, Union
from copy import deepcopy
import logging
from datetime import datetime
from pathlib import Path
import json
import yaml
import importlib

from ._basic import RunArgs, CommandParserFillerMixin, RunArgsBase
from .check import Check, SWUpdateDecisionMaker

from ..vendor import attr
from ..errors import (
    BadPillarDataError,
    PillarSetError,
    SWUpdateError,
    SWUpdateFatalError,
    ClusterMaintenanceEnableError,
    SWStackUpdateError,
    ClusterMaintenanceDisableError,
    HAPostUpdateError,
    ClusterNotHealthyError,
    SSLCertsUpdateError,
    ReleaseFileNotFoundError,
)
from ..config import (
    ALL_MINIONS,
    PRVSNR_FILEROOT_DIR, LOCAL_MINION,
    PRVSNR_USER_FILES_SSL_CERTS_FILE,
    PRVSNR_CORTX_COMPONENTS,
    PRVSNR_CLI_DIR,
    CONTROLLER_BOTH,
    SSL_CERTS_FILE,
    SEAGATE_USER_HOME_DIR, SEAGATE_USER_FILEROOT_DIR_TMPL,
    GroupChecks,
)
from ..pillar import (
    KeyPath,
    PillarKey,
    PillarUpdater,
    PillarResolver
)
# TODO IMPROVE EOS-8473
from ..utils import (
    load_yaml,
    dump_yaml_str,
)
from ..api_spec import api_spec
from ..salt import (
    StatesApplier,
    StateFunExecuter,
    State,
    YumRollbackManager,
    SaltJobsRunner, function_run,
    copy_to_file_roots, cmd_run as salt_cmd_run,
    local_minion_id
)
from ..hare import (
    cluster_maintenance_enable,
    cluster_maintenance_disable,
    apply_ha_post_update,
    ensure_cluster_is_healthy,
    consul_export
)
from ..salt_master import (
    config_salt_master,
    ensure_salt_master_is_running
)
from ..salt_minion import config_salt_minions
from .. import inputs, values

_mod = sys.modules[__name__]
logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsEmpty:
    pass


@attr.s(auto_attribs=True)
class RunArgsUpdate:
    targets: str = RunArgs.targets
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class RunArgsPillarGet(RunArgsBase):
    local: bool = RunArgs.local


@attr.s(auto_attribs=True)
class RunArgsPillarSet(RunArgsUpdate):
    local: bool = RunArgs.local


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
    targets: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "target(s) to install/update SSL certificate"
            }
        },
        default=ALL_MINIONS
    )
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class RunArgsConfigureCortx:
    component: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Component to configure",
                'choices': PRVSNR_CORTX_COMPONENTS
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
    _run_args_type = RunArgsPillarGet

    @classmethod
    def from_spec(
        cls, input_type: str = 'PillarKeysList'
    ):
        return cls(input_type=getattr(inputs, input_type))

    def run(
        self, *args, targets: str = ALL_MINIONS, local: bool = False,
        **kwargs
    ):
        pi_keys = self.input_type.from_args(*args, **kwargs)
        pillar_resolver = PillarResolver(targets=targets, local=local)

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

    _run_args_type = RunArgsPillarSet

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
    def run(
        self, *args, targets=ALL_MINIONS, dry_run=False, local=False, **kwargs
    ):
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
            pillar_updater = PillarUpdater(targets, local=local)
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
            logger.exception(f"Failed to set pillar with exception: {exc}")
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


@attr.s(auto_attribs=True)
class SetNTP(CommandParserFillerMixin):
    # TODO at least either pre or post should be defined
    input_type: Type[
        Union[inputs.ParamGroupInputBase, inputs.ParamDictItemInputBase]
    ]
    pre_states: List[State] = attr.Factory(list)
    post_states: List[State] = attr.Factory(list)

    _run_args_type = RunArgsUpdate

    # TODO input class type
    @classmethod
    def from_spec(cls, input_type: str, states: Dict):
        return cls(
            input_type=getattr(inputs, input_type),
            pre_states=[State(state) for state in states.get('pre', [])],
            post_states=[State(state) for state in states.get('post', [])]
        )

    def _apply(self, params, targets):
        pillar_updater = PillarUpdater(targets)

        pillar_updater.update(params)
        try:
            logger.debug('Applying pre states')
            StatesApplier.apply(self.pre_states)
            try:
                logger.debug('Applying pillar changes')
                pillar_updater.apply()

                logger.debug('Applying post states')
                StatesApplier.apply(self.post_states)
            except Exception:
                logger.warning(
                    "Starting Rollback: Result of "
                    "failure to apply pillar changes."
                )
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

    def _set_ctrl_ntp(self, params, targets):
        pillar_updater = PillarUpdater(targets)

        #TODO:
        #  1. ensure pillar data is updated at this stage
        #  2. confirm what pillar the NTP data is stored in
        #  3. test dry run
        #  4. test from CSM UI.

        pillar_updater.update(params)
        script = (
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        # TODO: Update logic to find enclosure_N based on current node_id
        enclosure = "enclosure-1"
        enclosure_pillar_path = KeyPath(f"storage/{enclosure}")
        system_pillar_path = KeyPath(f"system/ntp") #TODO: test
        ip = PillarKey(enclosure_pillar_path / 'controller/primary/ip')
        user = PillarKey(enclosure_pillar_path / 'controller/user')
        passwd = PillarKey(enclosure_pillar_path / 'controller/secret')

        ntp_server = PillarKey(system_pillar_path / 'time_server')
        timezone = PillarKey(system_pillar_path / 'time_zone')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd, ntp_server, timezone])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd, ntp_server, timezone):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
                )

        logger.info("Initiating NTP configuration on storage enclosure")
        logger.debug("Calling controller-cli utility to set NTP")
        try:
            StateFunExecuter.execute(
                'cmd.run',
                fun_kwargs=dict(
                    name=(
                        "{script} host -h {ip} -u {user} -p {passwd} "
                        "--ntp {ntp_server} '{timezone}'"
                        .format(
                            script=script,
                            ip=pillar[ip],
                            user=pillar[user],
                            passwd=pillar[passwd],
                            ntp_server=pillar[ntp_server],
                            timezone=pillar[timezone]
                        )
                    )
                )
            )
        except Exception:
            logger.exception('Failed to configure NTP on enclosure')
            raise

    def _run(self, params, targets):
        self._apply(params, targets)
        # Configure NTP only if the setup type is physical
        from .get_setup_info import GetSetupInfo
        setup_info = GetSetupInfo()
        server_type = setup_info._get_server_type().get('server_type')
        logger.debug(f"Server type: {server_type}")
        if server_type == "physical":
            self._set_ctrl_ntp(params, targets)

    def dynamic_validation(self, params, targets):
        pass

    # TODO
    # - class for pillar file
    # - caching (load once)
    def run(self, *args, targets=ALL_MINIONS, dry_run=False, **kwargs):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.input_type):
            params = args[0]
        else:
            params = self.input_type.from_args(*args, **kwargs)

        res = self.dynamic_validation(params, targets)

        if dry_run:
            return res

        return self._run(params, targets)



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
    def from_spec(cls, input_type: str, states: Dict):
        return cls(
            input_type=getattr(inputs, input_type),
            pre_states=[State(state) for state in states.get('pre', [])],
            post_states=[State(state) for state in states.get('post', [])]
        )

    def _apply(self, params, targets):
        pillar_updater = PillarUpdater(targets)

        pillar_updater.update(params)
        try:
            logger.debug('Applying pre states')
            StatesApplier.apply(self.pre_states)
            try:
                logger.debug('Applying pillar changes')
                pillar_updater.apply()

                logger.debug('Applying post states')
                StatesApplier.apply(self.post_states)
            except Exception:
                logger.warning(
                    "Starting Rollback: Result of "
                    "failure to apply pillar changes."
                )
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

    def _run(self, params, targets):
        self._apply(params, targets)

    def dynamic_validation(self, params, targets):
        pass

    # TODO
    # - class for pillar file
    # - caching (load once)
    def run(self, *args, targets=ALL_MINIONS, dry_run=False, **kwargs):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.input_type):
            params = args[0]
        else:
            params = self.input_type.from_args(*args, **kwargs)

        res = self.dynamic_validation(params, targets)

        if dry_run:
            return res

        return self._run(params, targets)


# TODO IMPROVE EOS-8940 move to separate module
def _ensure_update_repos_configuration(targets=ALL_MINIONS):
    logger.info("Ensuring update repos are configured")
    StatesApplier.apply(
        ['components.misc_pkgs.swupdate.repo'], targets
    )

    logger.info("Checking if yum repos are good")
    StatesApplier.apply(
        ['components.misc_pkgs.sw_update.repo.sanity_check'], targets
    )


def _pre_yum_rollback(
    rollback_ctx, exc_type, exc_value, exc_traceback
):
    if isinstance(
        exc_value, (HAPostUpdateError, ClusterNotHealthyError)
    ):
        try:
            logger.info(
                "Enabling cluster maintenance mode before rollback"
            )
            cluster_maintenance_enable()
        except Exception as exc:
            logger.error(
                "Encountered error while enabling "
                f"cluser maintenance mode: {exc}"
            )
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


def _consul_export(stage):
    # TODO make that configurable to turn off if not needed
    logger.info(f'Exporting consul [{stage}]')
    consul_export(fn_suffix=stage)


def _restart_salt_minions():
    logger.info("Restarting salt minions")
    salt_cmd_run(
        'systemctl restart salt-minion', background=True
    )


# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class SWUpdate(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, targets):  # noqa: C901 FIXME
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
        minion_conf_changes = None
        try:
            logger.info("Ensuring Cluster is Healthy")
            ensure_cluster_is_healthy()  # TODO: checker.run do that check too

            logger.info("Ensuring SW Update validatons are in place")
            checker = Check()
            try:
                check_res = checker.run(GroupChecks.SWUPDATE_CHECKS.value)
            except Exception as e:
                logger.warning("SW Update pre-flight checks errored with: "
                               f"{str(e)}")
            else:
                decision_maker = SWUpdateDecisionMaker()
                decision_maker.make_decision(check_result=check_res)

            _ensure_update_repos_configuration(targets)

            _consul_export('update-pre')

            with YumRollbackManager(
                targets,
                multiple_targets_ok=True,
                pre_rollback_cb=_pre_yum_rollback
            ) as rollback_ctx:
                logger.info(
                    'Enabling "smart maintenance" mode'
                )
                try:
                    cluster_maintenance_enable()
                except Exception as exc:
                    logger.error(
                        "Encountered error while enabling "
                        f"cluser maintenance mode: {exc}"
                    )
                    raise ClusterMaintenanceEnableError(exc) from exc

                logger.info(
                    "Updating SW stack packages and configuration"
                )
                try:
                    _update_component('provisioner', targets)

                    logger.info(
                        "Re-apply provisioner configuration to ensure "
                        "updated pillar value is reflected correctly."
                    )
                    _apply_provisioner_config(targets)

                    config_salt_master()

                    minion_conf_changes = config_salt_minions()

                    for component in (
                        'motr',
                        's3server',
                        'hare',
                        'ha.cortx-ha',
                        'sspl',
                        'uds',
                        'csm'
                    ):
                        _update_component(component, targets)
                except Exception as exc:
                    raise SWStackUpdateError(exc) from exc

                # SW stack now in "updated" state
                logger.info(
                    'Disabling "smart maintenance" mode'
                )
                try:
                    cluster_maintenance_disable()
                except Exception as exc:
                    logger.error(
                        "Encountered error while disabling "
                        f"cluser maintenance mode: {exc}"
                    )
                    raise ClusterMaintenanceDisableError(exc) from exc

                _consul_export('update-pre-ha-update')

                # call Hare to update cluster configuration
                logger.info(
                    "Updating Cluster configuration"
                )
                try:
                    apply_ha_post_update(targets)
                except Exception as exc:
                    raise HAPostUpdateError(exc) from exc

                _consul_export('update-post-ha-update')

                try:
                    ensure_cluster_is_healthy()
                except Exception as exc:
                    raise ClusterNotHealthyError(exc) from exc

                _consul_export('update-post')

                # NOTE that should be the very final step of the logic
                #      since salt client will be restarted so the current
                #      process might start to wait itself
                if minion_conf_changes:
                    # TODO: Improve salt minion restart logic
                    # please refer to task EOS-14114.
                    try:
                        logger.info("Restarting salt minions.")
                        _restart_salt_minions()
                    except Exception:
                        logger.exception(
                           "FAILED: Restarting salt minions. "
                           "For more info, check by executing command: \n"
                           "systemctl status salt-minion -l"
                        )

        except Exception as update_exc:
            # TODO TEST
            logger.exception("FAILED: SW Update")

            logger.info("Checking for Rollback")
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
                    logger.error(
                        "Disabling Cluster maintenance to fail gracefully"
                    )
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
                    logger.error(
                        "Rollback provisioner related configuration"
                    )
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

                            _consul_export('rollback-pre-ha-update')

                            apply_ha_post_update(targets)

                            _consul_export('rollback-post-ha-update')

                            ensure_cluster_is_healthy()

                            _consul_export('rollback-post')
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
            logger.error(f"Provided input '{source}' is not a file. "
                         "Please provide a valid file to proceed with FW Update.")
            raise ValueError(f"{source} is not a file")

        script = (
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        # TODO: Update logic to find enclosure_N based on current node_id
        enclosure = "enclosure-1"
        enclosure_pillar_path = KeyPath(f"storage/{enclosure}")
        ip = PillarKey(enclosure_pillar_path / 'controller/primary/ip')
        user = PillarKey(enclosure_pillar_path / 'controller/user')
        # TODO IMPROVE EOS-14361 mask secret
        passwd = PillarKey(enclosure_pillar_path / 'controller/secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
                )

        if dry_run:
            return

        logger.info("Initiating FW Update")

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
@attr.s(auto_attribs=True)
class GetReleaseVersion(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase
    _installed_rpms: List = attr.ib(init=False, default=None)

    @property
    def installed_rpms(self) -> List:
        if self._installed_rpms is None:
            exclude_rpms = 'cortx-py|prvsnr-cli'
            res = salt_cmd_run(f"rpm -qa|grep '^cortx-'|grep -Ev '{exclude_rpms}'",  # noqa: E501
                               targets=LOCAL_MINION)
            rpms = res[next(iter(res))].split("\n")
            self._installed_rpms = [f'{rpm}.rpm' for rpm in rpms if rpm]
        return self._installed_rpms

    def _get_rpms_from_release(self, source):
        return load_yaml(source)['COMPONENTS']

    def _compare_rpms_info(self, release_rpms):
        return (release_rpms and
                set(self.installed_rpms).issubset(release_rpms))

    def _get_release_info_path(self):
        release_repo = ''
        update_repo = PillarKey('release/update')
        pillar = PillarResolver(LOCAL_MINION).get([update_repo])
        pillar = next(iter(pillar.values()))
        release = pillar[update_repo]
        base_dir = Path(release['base_dir'])
        repos = release['repos']
        for release, source in reversed(list(repos.items())):
            release_repo = base_dir / f'{release}/RELEASE.INFO'
            if source == "iso":
                release_rpms = self._get_rpms_from_release(release_repo)
                if self._compare_rpms_info(release_rpms):
                    return release_repo

    def run(self, targets):
        update_path = self._get_release_info_path()
        if update_path:
            source = update_path
        else:
            source = Path("/etc/yum.repos.d/RELEASE_FACTORY.INFO")
        return json.dumps(load_yaml(source))


@attr.s(auto_attribs=True)
class GetFactoryVersion(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self, targets):
        source = "/etc/yum.repos.d/RELEASE_FACTORY.INFO"
        try:
            with open(source, 'r') as filehandle:
                return json.dumps(yaml.load(filehandle))
        except Exception as exc:
            raise ReleaseFileNotFoundError(exc) from exc


# TODO TEST
# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class SetSSLCerts(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSSLCerts

    def run(self, source, restart=False, targets=ALL_MINIONS, dry_run=False):  # noqa: E501, C901 FIXME

        source = Path(source).resolve()
        dest = PRVSNR_USER_FILES_SSL_CERTS_FILE
        time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        state_name = "components.misc_pkgs.ssl_certs"

        if not source.is_file():
            logger.error(f"Provided input '{source}' is not a file. "
                         "Please provide a valid SSL file source")
            raise ValueError(f"{source} is not a file")

        if dry_run:
            return

        try:
            # move cluster to maintenance mode
            try:
                cluster_maintenance_enable()
                logger.info('Cluster maintenance mode enabled')
            except Exception as exc:
                logger.error(
                    "Encountered error while enabling "
                    f"cluser maintenance mode: {exc}"
                )
                raise ClusterMaintenanceEnableError(exc) from exc

            copy_to_file_roots(source, dest)

            try:
                # backup old ssl certs to provisioner user files
                backup_file_name = copy_to_file_roots(
                    SSL_CERTS_FILE,
                    dest.parent /
                    '{}_{}'.format(
                        time_stamp,
                        dest.name))
                StatesApplier.apply([state_name], targets=targets)
                logger.info('SSL Certs Updated')

            except Exception as exc:
                logger.exception(f"FAILED: SSL certs apply due to {exc}")
                raise SSLCertsUpdateError(exc) from exc

            # disable cluster maintenance mode
            try:
                cluster_maintenance_disable()
                logger.info('Cluster recovered from maintenance mode')
            except Exception as exc:
                logger.error(
                    "Encountered error while disabling "
                    f"cluser maintenance mode: {exc}"
                )
                raise ClusterMaintenanceDisableError(exc) from exc

        except Exception as ssl_exc:
            logger.exception("FAILED: SSL Certs update")
            rollback_exc = None
            if isinstance(ssl_exc, ClusterMaintenanceEnableError):
                cluster_maintenance_disable(background=True)

            elif isinstance(ssl_exc, (
                    SSLCertsUpdateError, ClusterMaintenanceDisableError)):

                try:
                    logger.info('Restoring old SSL cert')
                    # restores old cert
                    copy_to_file_roots(backup_file_name, dest)
                    StatesApplier.apply([state_name], targets=targets)
                except Exception as exc:
                    logger.exception(
                        "Failed to apply backedup certs"
                    )
                    rollback_exc = exc
                else:
                    try:
                        cluster_maintenance_disable()
                    except Exception as exc:
                        logger.exception(
                            "Failed to recover Cluster after rollback"
                        )
                        rollback_exc = exc
            else:
                logger.warning('Unexpected error: {!r}'.format(ssl_exc))

            raise SSLCertsUpdateError(ssl_exc, rollback_error=rollback_exc)


# TODO TEST
@attr.s(auto_attribs=True)
class RebootServer(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self, targets):
        logger.info("Server Reboot")
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
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        # TODO:Update logic to find enclosure_N based on current node_id
        enclosure = "enclosure-1"
        enclosure_pillar_path = KeyPath(f"storage/{enclosure}")
        ip = PillarKey(enclosure_pillar_path / 'controller/primary/ip')
        user = PillarKey(enclosure_pillar_path / 'controller/user')
        # TODO IMPROVE EOS-14361 mask secret
        passwd = PillarKey(enclosure_pillar_path / 'controller/secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
                )

        logger.info("Controller Reboot")
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
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        # TODO:Update logic to find enclosure_N based on current node_id
        enclosure = "enclosure-1"
        enclosure_pillar_path = KeyPath(f"storage/{enclosure}")
        ip = PillarKey(enclosure_pillar_path / 'controller/primary/ip')
        user = PillarKey(enclosure_pillar_path / 'controller/user')
        # TODO IMPROVE EOS-14361 mask secret
        passwd = PillarKey(enclosure_pillar_path / 'controller/secret')

        pillar = PillarResolver(LOCAL_MINION).get([ip, user, passwd])
        pillar = next(iter(pillar.values()))

        for param in (ip, user, passwd):
            if not pillar[param] or pillar[param] is values.MISSED:
                raise BadPillarDataError(
                    'value for {} is not specified'.format(param.keypath)
                )

        logger.info("Controller Shutdown")
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
class ConfigureCortx(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureCortx

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

        logger.info(f"Creating new user: {uname}")
        home_dir = SEAGATE_USER_HOME_DIR / uname
        ssh_dir = home_dir / '.ssh'

        user_fileroots_dir = Path(
            PRVSNR_FILEROOT_DIR /
            SEAGATE_USER_FILEROOT_DIR_TMPL.format(uname=uname)
        )

        keyfile = user_fileroots_dir / f'id_rsa_{uname}'
        keyfile_pub = keyfile.with_name(f'{keyfile.name}.pub')

        # nodes = PillarKey('cluster/node_list')

        # nodelist_pillar = PillarResolver(LOCAL_MINION).get([nodes])
        # nodelist_pillar = next(iter(nodelist_pillar.values()))

        local_minion = local_minion_id()
        cluster_path = PillarKey('cluster')
        get_result = PillarResolver(local_minion).get([cluster_path])
        cluster_pillar = get_result[local_minion][cluster_path]
        nodes_list = [
            node for node in cluster_pillar.keys()
            if 'srvnode-' in node
        ]

        if (not cluster_pillar or
                cluster_pillar is values.MISSED):
            raise BadPillarDataError(
                'value for {} is not specified'.format(cluster_path.pi_key)
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
            for node in nodes_list:
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
                        SEAGATE_USER_FILEROOT_DIR_TMPL.format(uname=uname)
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

        # Update PATH just as a precaution
        StateFunExecuter.execute(
            'file.blockreplace',
            fun_kwargs=dict(
                name='~/.bashrc',
                marker_start='# DO NOT EDIT: Start',
                marker_end='# DO NOT EDIT: End',
                content='export PATH=$PATH:/usr/local/bin',
                append_if_not_found=True,
                append_newline=True,
                backup=False
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name='source ~/.bashrc'
            ),
            targets=targets
        )

        group_name = "csm-admin"
        logger.info(f"Creating a new group '{group_name}' with "
                    "limited access for csm admin users")
        StateFunExecuter.execute(
            'group.present',
            fun_kwargs=dict(
                name=group_name
            ),
            targets=targets
        )

        # Updating users/ dir permissions for graceful login
        StateFunExecuter.execute(
            'file.directory',
            fun_kwargs=dict(
                name=str(SEAGATE_USER_HOME_DIR),
                user='root',
                group='root',
                mode=755
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                name='/etc/sudoers.d/csm-admin',
                contents=('## Restricted access for csm group users \n'
                          '%csm-admin   ALL = NOPASSWD: '
                          '/usr/bin/tail, '
                          '/usr/sbin/ifup, '
                          '/usr/sbin/ifdown, '
                          '/usr/sbin/ip, '
                          '/usr/sbin/subscription-manager, '
                          '/usr/bin/cat, '
                          '/usr/bin/cd, '
                          '/usr/bin/ls, '
                          '/usr/sbin/pcs, '
                          '/usr/bin/salt, '
                          '/usr/local/bin/salt, '
                          '/usr/bin/salt-call, '
                          '/bin/salt-call, '
                          '/usr/local/bin/salt-call, '
                          '/usr/bin/yum, '
                          '/usr/bin/dir, '
                          '/usr/bin/cp, '
                          '/usr/bin/systemctl, '
                          '/opt/seagate/cortx/csm/lib/cortxcli, '
                          '/usr/bin/cortxcli, '
                          '/usr/bin/provisioner, '
                          '/var/log, '
                          '/tmp, '
                          '/usr/bin/lsscsi, '
                          '/usr/sbin/mdadm, '
                          '/usr/sbin/sfdisk, '
                          '/usr/sbin/mkfs, '
                          '/usr/bin/rsync, '
                          '/bin/rsync, '
                          '/usr/sbin/smartctl, '
                          '/usr/bin/ipmitool, '
                          '/usr/bin/sspl_bundle_generate, '
                          '/usr/bin/sspl_bundle_generate, '
                          '/usr/bin/rabbitmqctl, '
                          '/usr/sbin/rabbitmqctl, '
                          '/var/lib/rabbitmq, '
                          '/var/log/rabbitmq, '
                          f'{SEAGATE_USER_HOME_DIR}, '
                          f'{PRVSNR_CLI_DIR}/factory_ops/boxing/init, '
                          f'{PRVSNR_CLI_DIR}/factory_ops/unboxing/init'),
                create=True,
                replace=True,
                user='root',
                group='root',
                mode=440
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'user.present',
            fun_kwargs=dict(
                name=uname,
                password=passwd,
                hash_password=True,
                home=str(home_dir),
                groups=['csm-admin', 'prvsnrusers']
            ),
            targets=targets,
            secure=True
        )
        logger.info(
            'Setting up passwordless ssh for {uname} user on both the nodes'
            .format(
                uname=uname
            )
        )
        _passwordless_ssh()


commands = {}
for cmd_name, spec in api_spec.items():
    spec = deepcopy(api_spec[cmd_name])  # TODO
    cmd_cls = spec.pop('type')
    try:
        command = getattr(_mod, cmd_cls)
    except AttributeError:
        try:
            cmd_mod = importlib.import_module(
                f'provisioner.commands.{cmd_name}'
            )
        except Exception:
            logger.error(f"Failed to import provisioner.commands.{cmd_name}")
            raise
        command = getattr(cmd_mod, cmd_cls)
    commands[cmd_name] = command.from_spec(**spec)
