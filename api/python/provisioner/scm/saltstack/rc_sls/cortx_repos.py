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

from .base import ResourceSLS

from provisioner.resources import cortx_repos
from provisioner import config


logger = logging.getLogger(__name__)


# XXX validation after setup
class CortxReposSetupSLS(ResourceSLS):
    sls = 'repos'
    state_t = cortx_repos.CortxReposSetup

    @staticmethod
    def _iso_or_dir(path):
        return (
            path and (
                path.is_dir() or (path.is_file() and path.suffix == '.iso')
            )
        )

    @staticmethod
    def _add_3rd_parties(repos, deps_url):
        repos.update({
            # TODO hard-coded
            '3rd_party_epel': (
                f"{deps_url}/EPEL-7" if deps_url else None
            ),
            '3rd_party_saltstack': (
                f"{deps_url}/commons/saltstack-3001" if deps_url else None
            ),
            '3rd_party_glusterfs': (
                f"{deps_url}/commons/glusterfs" if deps_url else None
            )
        })

    def _prepare_release_pillar(
        self, deps_url, repos, python_repo=None
    ):
        return {
            'release': {
                'type': str(self.state.dist_type),
                'target_build': self.state.target_build,
                'deps_bundle_url': deps_url,
                'base': {
                    'repos': repos
                },
                'python_repo': python_repo
            }
        }

    def setup_roots_for_bundle(self, targets):
        file_roots = [self.state.cortx.parent]

        deps_bundle_url = (
            f"{self.state.target_build}/{config.CORTX_3RD_PARTY_ISO_DIR}"
        )

        repos = {
            config.CORTX_SINGLE_ISO_DIR: {
                'source': f"salt://{self.state.cortx.name}",
                'is_repo': False
            },
            config.CORTX_ISO_DIR: (
                f"{self.state.target_build}/{config.CORTX_ISO_DIR}"
            ),
            config.CORTX_3RD_PARTY_ISO_DIR: deps_bundle_url
        }

        self._add_3rd_parties(repos, deps_bundle_url)

        if self.state.os:
            repos[config.OS_ISO_DIR] = f"salt://{self.state.os.name}"
            file_roots.append(self.state.os.parent)
        else:
            repos[config.OS_ISO_DIR] = None

        python_repo = (
            f"{self.state.target_build}/{config.CORTX_PYTHON_ISO_DIR}"
            if self.state.py_index else None
        )
        pillar = self._prepare_release_pillar(
            deps_bundle_url, repos, python_repo
        )

        return file_roots, pillar

    def setup_roots_for_cortx(self, targets):
        repos = {}
        file_roots = []

        # XXX copy validation routine from SetSWUpdateRepo
        if self._iso_or_dir(self.state.cortx):
            repos[config.CORTX_ISO_DIR] = f"salt://{self.state.cortx.name}"
            file_roots.append(self.state.cortx.parent)
        else:
            repos[config.CORTX_ISO_DIR] = str(self.state.cortx)

        # XXX copy validation routine from SetSWUpdateRepo
        if self._iso_or_dir(self.state.deps):
            deps_url = 'file://{}'.format(
                config.PRVSNR_CORTX_REPOS_BASE_DIR /
                config.CORTX_3RD_PARTY_ISO_DIR
            )
            repos[config.CORTX_3RD_PARTY_ISO_DIR] = (
                f"salt://{self.state.deps.name}"
            )
            file_roots.append(self.state.deps.parent)
        elif self.state.deps:  # url
            deps_url = self.state.deps
            repos[config.CORTX_3RD_PARTY_ISO_DIR] = str(self.state.deps)
        else:
            deps_url = None
            repos[config.CORTX_3RD_PARTY_ISO_DIR] = None

        self._add_3rd_parties(repos, deps_url)

        if self.state.os:
            if self._iso_or_dir(self.state.os):
                repos[config.OS_ISO_DIR] = f"salt://{self.state.os.name}"
                file_roots.append(self.state.os.parent)
            else:
                repos[config.OS_ISO_DIR] = str(self.state.os)
        else:
            repos[config.OS_ISO_DIR] = None

        pillar = self._prepare_release_pillar(deps_url, repos)

        return file_roots, pillar

    def setup_roots(self, targets):
        super().setup_roots()

        if self.state.dist_type == config.DistrType.BUNDLE:
            file_roots, pillar = self.setup_roots_for_bundle(targets)
        else:
            file_roots, pillar = self.setup_roots_for_cortx(targets)

        if file_roots:
            self.client.add_file_roots(file_roots)

        if pillar:
            self.client.pillar_set(pillar)

        # TODO IMPROVE DOC EOS-12076 Iso installation logic:
        #   - iso files are copied to user local file roots on all remotes
        #     (TODO consider user shared, currently glusterfs
        #      is not enough trusted)
        #   - iso is mounted to a location inside user local data
        #   - a repo file is created and pointed to the mount directory
        # TODO EOS-12076 IMPROVE hard-coded
        # do not copy ISO for the node where we are now already

#    def run(self):
#        if (
#            self.field_setup
#            and self.source == 'iso'
#            and (
#                not self.iso_os
#                or self.iso_os == config.PRVSNR_OS_ISO
#            )
#            and (
#                self.iso_cortx == config.PRVSNR_CORTX_SINGLE_ISO
#                or (
#                    self.iso_cortx == config.PRVSNR_CORTX_ISO and
#                    self.iso_deps == config.PRVSNR_CORTX_DEPS_ISO
#                )
#            )
#        ):
#            # FIXME it is valid only for replace_node logic,
#            #       not good to rely on some specific case here
#            # FIXME hardcoded pillar key
#            ssh_client.state_apply(
#                'repos', targets=self.primary.minion_id,
#                fun_kwargs={
#                    'pillar': {
#                        'skip_iso_copy': True
#                    }
#                }
#            )
#            # NOTE for now salt-ssh supports only glob and regex targetting
#            # https://docs.saltstack.com/en/latest/topics/ssh/#targeting-with-salt-ssh  # noqa: E501
#            ssh_client.state_apply(
#                'repos',
#                targets='|'.join([
#                    node.minion_id for node in self.secondaries
#                ]),
#                tgt_type='pcre'
#            )
#        else:
#            # copy ISOs onto all remotes and mount
#            ssh_client.state_apply('repos')
#
#        ssh_client.state_apply('cortx_repos')  # FIXME EOS-12076
#
#        if not self.pypi_repo:
#            logger.info("Setting up custom python repository")
#            ssh_client.state_apply('repos.pip_config')
