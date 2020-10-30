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
    SaltCmdResultError,
    SWUpdateRepoSourceError
)
from ..config import (
    ALL_MINIONS, PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR,
    PRVSNR_FILEROOT_DIR, LOCAL_MINION,
    PRVSNR_USER_FILES_SSL_CERTS_FILE,
    PRVSNR_CORTX_COMPONENTS,
    PRVSNR_CLI_DIR,
    CONTROLLER_BOTH,
    SSL_CERTS_FILE,
    SEAGATE_USER_HOME_DIR, SEAGATE_USER_FILEROOT_DIR_TMPL,
    REPO_CANDIDATE_NAME,
    RELEASE_INFO_FILE,
    ReleaseInfo
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


class CommandParserFillerMixin:
    _run_args_type = RunArgsBase

    @classmethod
    def _run_args_types(cls):
        ret = cls._run_args_type
        return ret if type(ret) is list else [ret]

    @classmethod
    def fill_parser(cls, parser):
        for arg_type in cls._run_args_types():
            inputs.ParserFiller.fill_parser(arg_type, parser)

    @classmethod
    def from_spec(cls):
        return cls()

    @classmethod
    def extract_positional_args(cls, kwargs):
        for arg_type in cls._run_args_types():
            return inputs.ParserFiller.extract_positional_args(
                arg_type, kwargs
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
    def from_spec(cls, input_type: str, states: Dict):
        return cls(
            input_type=getattr(inputs, input_type),
            pre_states=[State(state) for state in states.get('pre', [])],
            post_states=[State(state) for state in states.get('post', [])]
        )

    def _run(self, params, targets):
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
                logger.warning('Failed to apply changes, starting rollback')
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


# assumtions / limitations
#   - support only for ALL_MINIONS targetting TODO ??? why do you think so
#
#

# set/remove the repo:
#   - call repo reset logic for salt-minions:
#       - remove repo config for yum
#       - unmount repo if needed
#       - remove repo dir/iso file if needed TODO
#   - call repo reset logic for salt-master:
#       - remove local dir/file from salt user file root (if needed)
@attr.s(auto_attribs=True)
class SetSWUpdateRepo(Set):
    # TODO at least either pre or post should be defined
    input_type: Type[inputs.SWUpdateRepo] = inputs.SWUpdateRepo

    @staticmethod
    def _prepare_repo_for_apply(
        repo: inputs.SWUpdateRepo, enabled: bool = True
    ):
        # if local - copy the repo to salt user file root
        # TODO consider to use symlink instead
        if repo.is_local():
            dest = PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR / repo.release

            if not repo.is_dir():  # iso file
                dest = dest.with_name(dest.name + '.iso')

            logger.debug(f"Copying {repo.source} to file roots")
            copy_to_file_roots(repo.source, dest)

            if not enabled:
                repo.repo_params = dict(enabled=False)

    @staticmethod
    def _get_mount_dir():
        """
        Return the base mount directory of ISO repo candidate based on pillars
        values configuration

        :return: Path to repo candidate mount destination
        """
        update_dir = PillarKey('release/update/base_dir')

        pillar = PillarResolver(LOCAL_MINION).get((update_dir,))

        pillar = pillar.get(local_minion_id())  # type: dict

        if (not pillar[update_dir] or
                pillar[update_dir] is values.MISSED):
            raise BadPillarDataError('value for '
                                     f'{update_dir.keypath} '
                                     'is not specified')

        return Path(pillar[update_dir])

    @staticmethod
    def _does_repo_exist(release: str) -> bool:
        """
        Check if passed `release` repo is listed among yum repositories
        (enabled or disabled)

        :param str release: release to check existence
        :return: True if `release` listed in yum repositories
        """
        # From yum manpage:
        # You  can  pass repo id or name arguments, or wildcards which to match
        # against both of those. However if the id or name matches exactly
        # then the repo will be listed even if you are listing enabled repos
        # and it is disabled.
        cmd = (f"yum repoinfo {release} 2>/dev/null | grep '^Repo\\-id' | "
               "awk -F ':' '{ print $NF }'")

        res = salt_cmd_run(cmd, targets=local_minion_id(),
                           fun_kwargs=dict(python_shell=True))

        find_repo = res[local_minion_id()].strip().split("/")[0]

        if find_repo:
            logger.debug(f"Found '{release}' repository in repolist")
        else:
            logger.debug(f"Didn't find '{release}' repository in repolist")

        return bool(find_repo)

    @staticmethod
    def _is_repo_enabled(release) -> bool:
        """
        Verifies if `release` repo listed in enabled yum repo list

        :param release: repo release for check
        :return: True if `release` listed in enabled yum repo list and False
                 otherwise
        """
        cmd = (
            "yum repoinfo enabled -q 2>/dev/null | grep '^Repo\\-id' "
            "| awk  -F ':' '{print $NF}'"
        )
        res = salt_cmd_run(
            cmd, targets=local_minion_id(), fun_kwargs=dict(python_shell=True)
        )
        repos = [
            repo.strip().split('/')[0]
            for repo in res[local_minion_id()].split()
        ]
        logger.debug(f"Found enabled repositories: {repos}")
        return release in repos

    @staticmethod
    def _check_repo_is_valid(release):
        """
        Validate if provided `release` repo is well-formed yum repository

        :param release:
        :return: None if the repo is correct. Otherwise raise
                 `SaltCmdResultError` if `release` repo malformed.
        """
        cmd = (f"yum --disablerepo='*' --enablerepo='sw_update_{release}' "
               "list available")

        salt_cmd_run(cmd, targets=LOCAL_MINION)

    def dynamic_validation(self, params: inputs.SWUpdateRepo, targets: str):  # noqa: C901, E501
        repo = params

        if repo.is_special():
            logger.info(
                "Skipping update repo validation for special value: "
                f"{repo.source}"
            )
            return

        logger.info(
            f"Validating update repo: release {repo.release}, "
            f"source {repo.source}"
        )

        candidate_repo = inputs.SWUpdateRepo(
            REPO_CANDIDATE_NAME, repo.source
        )

        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        if self._does_repo_exist(f'sw_update_{candidate_repo.release}'):
            logger.warning(
                'other repo candidate was found, proceeding with force removal'
            )
            # TODO IMPROVE: it is not enough it may lead to locks when
            #  provisioner doesn't unmount `sw_update_candidate` repo
            # raise SWUpdateError(reason="Other repo candidate was found")

        # TODO IMPROVE
        #   - makes sense to try that only on local minion,
        #     currently it's not convenient since may lead to
        #     mess in release.sls pillar between all and specific
        #     minions
        try:
            logger.debug(
                "Configuring update candidate repo for validation"
            )
            self._prepare_repo_for_apply(candidate_repo, enabled=False)

            super()._run(candidate_repo, targets)

            # general check from pkg manager point of view
            try:
                self._check_repo_is_valid(candidate_repo.release)
            except SaltCmdResultError as exc:
                raise SWUpdateRepoSourceError(
                    str(repo.source), f"malformed repo: '{exc}'"
                )

            # TODO: take it from pillar
            # the repo includes metadata file
            iso_mount_dir = self._get_mount_dir() / REPO_CANDIDATE_NAME
            release_file = f'{iso_mount_dir}/{RELEASE_INFO_FILE}'
            try:
                metadata = load_yaml(release_file)
            except Exception as exc:
                raise SWUpdateRepoSourceError(
                    str(repo.source),
                    f"Failed to load '{RELEASE_INFO_FILE}' file: {exc}"
                )
            else:
                repo.metadata = metadata
                logger.debug(f"Resolved metadata {metadata}")

            # the metadata file includes release info
            # TODO IMPROVE: maybe it is good to verify that 'RELEASE'-field
            #  well formed
            release = metadata.get(ReleaseInfo.RELEASE.value, None)
            if release is None:
                try:
                    release = (
                        f'{metadata[ReleaseInfo.VERSION.value]}-'
                        f'{metadata[ReleaseInfo.BUILD.value]}'
                    )
                except KeyError:
                    raise SWUpdateRepoSourceError(
                        str(repo.source),
                        f"No release data found in '{RELEASE_INFO_FILE}'"
                    )

            # there is no the same release repo is already active
            if self._is_repo_enabled(f'sw_update_{release}'):
                raise SWUpdateRepoSourceError(
                    str(repo.source),
                    (
                        f"SW update repository for the release "
                        f"'{release}' has been already enabled"
                    )
                )

            # TODO IMPROVE
            #   - new version is higher then currently installed

            # Optional: try to get current version of the repository
            # TODO: use digit-character regex to retrieve repository release
            # cmd = ('yum repoinfo enabled | '
            #        'sed -rn "s/Repo-id\\s+:.*sw_update_(.*)$/\\1/p"')

            repo.release = release
        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED
            logger.info("Post-validation cleanup")
            super()._run(candidate_repo, targets)

        return repo.metadata

    # TODO rollback
    def _run(self, params: inputs.SWUpdateRepo, targets: str):
        repo = params

        logger.info(f"Configuring update repo: release {repo.release}")
        self._prepare_repo_for_apply(repo, enabled=True)

        # call default set logic (set pillar, call related states)
        super()._run(repo, targets)
        return repo.metadata


# TODO IMPROVE EOS-8940 move to separate module
def _ensure_update_repos_configuration(targets=ALL_MINIONS):
    logger.info("Ensure update repos are configured")
    StatesApplier.apply(
        ['components.misc_pkgs.swupdate.repo'], targets
    )

    logger.info("Check yum repos are good")
    StatesApplier.apply(
        ['components.misc_pkgs.eosupdate.repo.sanity_check'], targets
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
            ensure_cluster_is_healthy()

            _ensure_update_repos_configuration(targets)

            _consul_export('update-pre')

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
                # disable "smart maintenance" mode
                try:
                    cluster_maintenance_disable()
                except Exception as exc:
                    raise ClusterMaintenanceDisableError(exc) from exc

                _consul_export('update-pre-ha-update')

                # call Hare to update cluster configuration
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
                        _restart_salt_minions()
                    except Exception:
                        logger.exception('failed to restart salt minions')

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
            raise ValueError('{} is not a file'.format(source))

        script = (
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        # TODO IMPROVE EOS-14361 mask secret
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
            raise ValueError('{} is not a file'.format(source))

        if dry_run:
            return

        try:
            # move cluster to maintenance mode
            try:
                cluster_maintenance_enable()
                logger.info('Cluster maintenance mode enabled')
            except Exception as exc:
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
                logger.exception(
                    "Failed to apply certs")
                raise SSLCertsUpdateError(exc) from exc

            # disable cluster maintenance mode
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

            elif isinstance(ssl_exc, (
                    SSLCertsUpdateError, ClusterMaintenanceDisableError)):

                try:
                    logger.info('Restoring old SSL cert ')
                    # restores old cert
                    copy_to_file_roots(backup_file_name, dest)
                    StatesApplier.apply([state_name], targets=targets)
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

            raise SSLCertsUpdateError(ssl_exc, rollback_error=rollback_exc)


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
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        # TODO IMPROVE EOS-14361 mask secret
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
            PRVSNR_FILEROOT_DIR /
            'components/controller/files/scripts/controller-cli.sh'
        )

        controller_pi_path = KeyPath('storage_enclosure/controller')
        ip = PillarKey(controller_pi_path / 'primary_mc/ip')
        user = PillarKey(controller_pi_path / 'user')
        # TODO IMPROVE EOS-14361 mask secret
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

        home_dir = SEAGATE_USER_HOME_DIR / uname
        ssh_dir = home_dir / '.ssh'

        user_fileroots_dir = Path(
            PRVSNR_FILEROOT_DIR /
            SEAGATE_USER_FILEROOT_DIR_TMPL.format(uname=uname)
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

        # Creating a new group with limited access for csm admin users
        StateFunExecuter.execute(
            'group.present',
            fun_kwargs=dict(
                name='csm-admin'
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
                          '/opt/seagate/cortx/sspl/bin/sspl_bundle_generate, '
                          '/opt/seagate/cortx/sspl/lib/sspl_bundle_generate, '
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
