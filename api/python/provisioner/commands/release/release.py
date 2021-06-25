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
import requests

from configparser import ConfigParser
from pathlib import Path

from typing import Union, Optional, ClassVar
from urllib.parse import urlparse, ParseResult

from provisioner.vendor import attr
from provisioner import config, utils, errors
from provisioner.salt import (
    local_minion_id
)
from provisioner.pillar import (
    PillarKey,
    PillarResolver
)

logger = logging.getLogger(__name__)


def release_url_converter(url: Union[str, Path, ParseResult]):
    if isinstance(url, Path):
        return urlparse(f"file://{url.resolve()}")
    elif isinstance(url, str):
        return urlparse(url)
    else:
        return url


@attr.s(auto_attribs=True)
class CortxReleaseUrl:
    url: Union[str, ParseResult] = attr.ib(
        converter=release_url_converter,
        validator=attr.validators.instance_of(ParseResult),
    )

    def __str__(self) -> str:
        return self.url.geturl()

    @property
    def path(self) -> str:
        # Note. if 'netloc' is defined 'path' will always start with '/'
        return f"{self.url.netloc}{self.url.path}"

    @property
    def is_local(self) -> str:
        return self.url.scheme == 'file'


@attr.s(auto_attribs=True)
class CortxReleaseInfo:
    metadata: dict

    @property
    def version(self):
        # the metadata file includes release info
        # TODO IMPROVE: maybe it is good to verify that 'RELEASE'-field
        #  well formed
        return self.metadata.get(
            config.ReleaseInfo.RELEASE.value,
            (
                f"{self.metadata[config.ReleaseInfo.VERSION.value]}-"
                f"{self.metadata[config.ReleaseInfo.BUILD.value]}"
            )
        )


@attr.s(auto_attribs=True)
class CortxRelease:
    _factory_release: ClassVar[Optional['CortxRelease']] = None

    _version: Optional[str] = None
    _metadata: Optional[dict] = attr.ib(
        default=None,
        converter=attr.converters.optional(CortxReleaseInfo)
    )
    _metadata_uri: Optional[CortxReleaseUrl] = attr.ib(
        default=None,
        converter=attr.converters.optional(CortxReleaseUrl)
    )

    _iso_version: str = attr.ib(init=False, default=None)

    @classmethod
    def factory_release(cls):
        if cls._factory_release is None:
            cls._factory_release = cls(
                metadata_uri=config.CORTX_RELEASE_FACTORY_INFO_PATH
            )
        return cls._factory_release

    def __attrs_post_init__(self):
        # rules:
        # - either one of params should be defined
        # - url has the highest priority, other params are ignored
        #   if url is defined
        # - if both version and metadata are defined they should
        #   be consistent
        if self._metadata_uri:
            if self._version:
                logger.warning(
                    "'version' parameter would be ignored since"
                    "'metadata_uri' is provided"
                )
                self._version = None
            if self._metadata:
                logger.warning(
                    "'metadata' parameter would be ignored since"
                    "'metadata_uri' is provided"
                )
                self._metadata = None
        elif self._metadata:
            if self._version and self._version != self._metadata.version:
                raise ValueError(
                    "'version' parameter '{self._version}' doesn't match "
                    "metadata info: '{self._metadata.version}'"
                )
        elif not self._version:
            raise ValueError(
                "either 'version' or 'metadata' or 'metadata_uri' "
                "should be defined"
            )

    @property
    def is_factory(self):
        factory_release = self.factory_release()
        return (
            self is factory_release
            or self.version == factory_release.version
        )

    @property
    def iso_version(self) -> config.ISOVersion:
        """
        Return version of ISO bundle scheme for the release

        Returns
        -------
        config.ISOVersion:
            return version of ISO bundle scheme for the release

        """
        if self._iso_version is None:
            if self.is_factory:
                # FIXME improve to support newer versions for deployment
                self._iso_version = config.ISOVersion.VERSION1
            else:
                # search in upgrade releases
                pillar_path = f'release/upgrade/repos/{self.version}'
                pillars = PillarResolver(local_minion_id()).get(
                    [PillarKey(pillar_path)],
                    fail_on_undefined=True
                )

                upgrade_release = pillars[local_minion_id()][
                    PillarKey(pillar_path)
                ]
                release_data = upgrade_release.get(self.version)
                # NOTE: release_data can be None after applying
                #  remove_swupgrade_repo command
                if (
                    isinstance(release_data, dict)
                    and 'version' in release_data
                ):
                    self._iso_version = config.ISOVersion(
                        release_data['version']
                    )
                else:
                    # FIXME: it may be remote repo
                    self._iso_version = config.ISOVersion.VERSION1

        return self._iso_version

    @property
    def metadata_uri(self) -> CortxReleaseUrl:
        """
        Return URL to a Cortx repository metadata

        Returns
        -------
        CortxReleaseUrl:
            return URL to a Cortx repository metadata file

        """
        if self._metadata_uri is None:
            if self.is_factory:
                self._metadata_uri = CortxReleaseUrl(
                    f"file://{config.CORTX_RELEASE_FACTORY_INFO_PATH}"
                )
            else:
                # upgrade release
                if self.iso_version == config.ISOVersion.VERSION1:
                    repo = f"sw_upgrade_{config.CORTX_ISO_DIR}_{self.version}"
                    release_file = config.RELEASE_INFO_FILE
                else:
                    repo = (
                        f"sw_upgrade_{config.UpgradeReposVer2.CORTX.value}"
                        f"_{self.version}"
                    )
                    release_file = config.CORTX_RELEASE_INFO_FILE

                c_parser = ConfigParser()
                c_parser.read(f'/etc/yum.repos.d/{repo}.repo')
                repo_uri = c_parser.get(repo, 'baseurl', fallback=None)

                if repo_uri is None:
                    raise ValueError(
                        f"'baseurl' option is missed for repo: '{repo}'"
                    )

                self._metadata_uri = CortxReleaseUrl(
                    f'{repo_uri}/{release_file}'
                )

        return self._metadata_uri

    def load_metadata(self):
        """
        Load the metadata from metadata url

        Returns
        -------
        dict:
            dictionary with Cortx repository metadata (content of RELEASE.INFO
            file)
        """
        try:
            if self.metadata_uri.is_local:
                metadata = utils.load_yaml(self.metadata_uri.path)
            else:
                r = requests.get(str(self.metadata_uri))
                metadata = utils.load_yaml_str(r.content.decode("utf-8"))
        except Exception as exc:
            raise errors.SWUpdateRepoSourceError(
                str(self.metadata_uri),
                f"Failed to load '{self.metadata_uri}' file: {exc}"
            )

        return metadata

    @property
    def release_info(self) -> CortxReleaseInfo:
        """
        Return release info object

        Returns
        -------
        CortxReleaseInfo:
            return release info object

        """
        if self._metadata is None:
            self._metadata = CortxReleaseInfo(self.load_metadata())
        return self._metadata

    @property
    def metadata(self) -> dict:
        """
        Return release metadata

        Returns
        -------
        dict:
            return release metadata

        """
        return self.release_info.metadata

    @property
    def version(self):
        if self._version is None:
            self._version = self.release_info.version
        return self._version
