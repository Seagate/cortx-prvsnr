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


# import logging
#
#
# logger = logging.getLogger(__name__)
# _mod = sys.modules[__name__]
#
#
# @attr.s(auto_attribs=True)
# class Provisioner(Resource):
#     name = 'provisioner'
#
#
# class ProvisionerSLS(ResourceSLS):
#     resource = Provisioner
#
#
# @attr.s(auto_attribs=True)
# class Install(ProvisionerSLS):
#     name = 'install'
#     sls = 'provisioner.install'
#
#
# @attr.s(auto_attribs=True)
# class InstallLocal(ProvisionerSLS):
#     name = 'install-local'
#     sls = 'provisioner.install.local'
#
#     local_repo: str = RunArgsSetup.local_repo
#     prvsnr_version: str = RunArgsSetup.prvsnr_version
#
#     def _prepare_local_repo(self, repo_dir: Path):
#         # ensure parent dirs exists in profile file root
#         run_subprocess_cmd(['rm', '-rf', str(repo_dir)])
#         repo_dir.mkdir(parents=True, exist_ok=True)
#
#         # (locally) prepare tgz
#         repo_tgz_path = repo_dir.parent / 'repo.tgz'
#         repo_tgz(
#             repo_tgz_path,
#             project_path=self.local_repo,
#             version=self.prvsnr_version,
#             include_dirs=['pillar', 'srv', 'files', 'api', 'cli']
#         )
#
#         # extract archive locally
#         run_subprocess_cmd(
#             ['tar', '-zxf', str(repo_tgz_path), '-C', str(repo_dir)]
#         )
#
#         # TODO IMPROVE use salt caller and file-managed instead
#         # set proper cluster.sls from template
#         cluster_sls_sample_path = (
#             repo_dir / 'pillar/components/samples/dualnode.cluster.sls'
#         )
#         cluster_sls_path = repo_dir / 'pillar/components/cluster.sls'
#         run_subprocess_cmd(
#             [
#                 'cp', '-f',
#                 str(cluster_sls_sample_path),
#                 str(cluster_sls_path)
#             ]
#         )
#         repo_tgz_path.unlink()
#
#     def setup_roots(self, targets):
#         logger.info("Preparing local repo for a setup")
#         # TODO IMPROVE EOS-8473 hard coded
#         self._prepare_local_repo(
#             self,
#             salt_client.fileroot_path / 'provisioner/files/repo'
#         )
#
#
#
# @attr.s(auto_attribs=True)
# class FactoryProfile(ProvisionerSLS):
#     name = 'factory_profile'
#     sls = 'provisioner.factory_profile'
#
#     run_args: RunArgsSetupProvisionerGeneric
#     base_dir: Path
#     factory_profile_dir: Path
#
#     def _gen_factory_setup_pillar(self):
#         fdata_pi_key = 'factory_setup'
#
#         fdata_pillar = self.salt_client.pillar_get(
#             fdata_pi_key, local_minion_id
#         )
#
#         if fdata_pillar:
#             return
#
#         logger.info("Preparing setup pillar")  # DONE
#
#         # TODO IMPROVE here the setup pillar would have partial
#         #      duplication of release pillar (e.g. target build)
#         fdata_pillar = attr.asdict(run_args)
#         # TODO IMPROVE EOS-13686 more clean way
#         if fdata_pillar['dist_type']:
#             fdata_pillar['dist_type'] = fdata_pillar['dist_type'].value
#         if fdata_pillar['local_repo']:
#             fdata_pillar['local_repo'] = str(fdata_pillar['local_repo'])
#         if fdata_pillar['iso_os']:
#             fdata_pillar['iso_os'] = str(config.PRVSNR_OS_ISO)
#         if fdata_pillar['iso_cortx']:
#             if fdata_pillar['iso_cortx_deps']:
#                 fdata_pillar['iso_cortx'] = str(config.PRVSNR_CORTX_ISO)
#                 fdata_pillar['iso_cortx_deps'] = str(
#                     config.PRVSNR_CORTX_DEPS_ISO
#                 )
#             else:
#                 fdata_pillar['iso_cortx'] = str(config.PRVSNR_CORTX_SINGLE_ISO)
#         fdata_pillar.pop('bootstrap_key')
#         fdata_pillar = dict(factory_setup=fdata_pillar)
#         dump_yaml(pillar_path,  fdata_pillar)
#
#         salt_client.pillar_set([(factory_data_pi_key, fdata_pillar)])
#
#     def _gen_factory_profile(self):
#         logger.info("Preparing factory profile")
#         # XXX hard coded
#         for path in ('srv/salt', 'srv/pillar', '.ssh'):
#             _path = self.factory_profile_dir / path
#             run_subprocess_cmd(['rm', '-rf',  str(_path)])
#             _path.parent.mkdir(parents=True, exist_ok=True)
#             run_subprocess_cmd(
#                 [
#                     'cp', '-r',
#                     str(self.base_dir / path),
#                     str(_path.parent)
#                 ]
#             )
#
#         run_subprocess_cmd([
#             'rm', '-rf',
#             str(
#                 self.factory_profile_dir /
#                 'srv/salt/provisioner/files/repo'  # XXX hard coded
#             )
#         ])
#
#     def setup_roots(self):
#         self._gen_factory_setup_pillar()
#         self._gen_factory_profile()
#
#
# @attr.s(auto_attribs=True)
# class PillarSetup(ProvisionerSLS):
#     name = 'pillar_setup'
#     sls = None
#
#     METADATA_PI_KEY = 'pi_key'
#
#     dist_type: Union[str, _PrvsnrValue] = attr_ib(
#         default=UNCHANGED,
#         metadata={METADATA_PI_KEY: 'release/type'}
#     )
#     deps_bundle_url: Union[str, _PrvsnrValue] = attr_ib(
#         default=UNCHANGED,
#         metadata={METADATA_PI_KEY: 'release/deps_bundle_url'}
#     )
#     target_build: Union[str, _PrvsnrValue] = attr_ib(
#         default=UNCHANGED,
#         metadata={METADATA_PI_KEY: 'release/target_build'}
#     )
#
#     def setup_roots(self):
#         pillar_updates = []
#         fields_dict = attr.fields_dict(type(self))
#
#         logger.info("Updating production data")
#         for key, value in attr.asdict(self):
#             if value != UNCHANGED:
#                 pillar_updates.append(
#                     (fields_dict[key].metadata[self.METADATA_PI_KEY], value)
#                 )
#
#         logger.debug(f"Pillar data to update: {pillar_updates}")
#
#         if pillar_updates:
#             salt_client.pillar_set(pillar_updates)
#
#         # XXX ? always regenerated
#         logger.info(f"Generating a password for the service user")
#         password = str(uuid.uuid4()).split('-')[0]
#         salt_client.pillar_set(
#             [('system/service_user/password', password)], secure=True
#         )
#
#
# @attr.s(auto_attribs=True)
# class ReleaseInfo(ProvisionerSLS):
#     name = 'release_info'
#     sls = 'provisioner.release_info'
