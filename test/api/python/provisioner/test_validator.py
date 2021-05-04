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
import pytest
from unittest.mock import patch, mock_open, PropertyMock
import hashlib
import pathlib
import yaml

from provisioner.commands.validator import (HashSumValidator,
                                            ReleaseInfoValidator)
from provisioner.config import HashType, ContentType
from provisioner.errors import ValidationError


SINGLE_ISO_PATH = "/path/to/single.iso"

SINGLE_ISO_CONTENT = b'''
Some SW Upgrade single ISO content
Some SW Upgrade single ISO content
Some SW Upgrade single ISO content
'''

RELEASE_INFO = '''
VERSION: 2.0.1
BUILD: 277
DATETIME: Wed Mar  3 10:02:21 UTC 2021
KERNEL: 5.10.19-200.fc33.x86_64
NAME: CORTX
OS: Red Hat Enterprise Linux Server release 7.7 (Maipo)
COMPONENTS:
- cortx-csm_agent-2.0.0-1.noarch.rpm
- cortx-ha-2.0.0-1.noarch.rpm
- cortx-hare-2.0.0-1.noarch.rpm
- cortx-sspl-2.0.0-1.noarch.rpm
- uds-pyi-2.0.0-1.noarch.rpm
- cortx-cli-2.0.0-1.noarch.rpm
- cortx-sspl-test-2.0.0-1.noarch.rpm
- cortx-csm_web-2.0.0-1.noarch.rpm
- cortx-motr-2.0.0-1.noarch.rpm
- cortx-s3iamcli-2.0.0-1.noarch.rpm
- cortx-s3server-2.0.0-1.noarch.rpm
'''

CONTENT_LOADER_IMPORT_PATH = ('provisioner.commands.validator.'
                              'ContentFileValidator._CONTENT_LOADER')


def read_file(file_name):
    with open(file_name, "rb") as fh:
        while True:
            data = fh.read(4096)
            if not data:
                break
            yield data  # return bytes


def md5(file_name):
    md5_hash = hashlib.md5()
    for chunk in read_file(file_name):
        md5_hash.update(chunk)
    return md5_hash.hexdigest()


def sha256(file_name):
    sha256_hash = hashlib.sha256()
    for chunk in read_file(file_name):
        sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def sha512(file_name):
    sha512_hash = hashlib.sha512()
    for chunk in read_file(file_name):
        sha512_hash.update(chunk)
    return sha512_hash.hexdigest()


# NOTE: we can use here pytest_mock.plugin.MockFixture
def test_hash_sum_validator():
    with patch("builtins.open", mock_open(read_data=SINGLE_ISO_CONTENT)):

        assert open(SINGLE_ISO_PATH, 'r').read() == SINGLE_ISO_CONTENT

        # TEST: md5 hash
        md5_hash = md5(SINGLE_ISO_PATH)

        hash_validator = HashSumValidator(hash_sum=md5_hash,
                                          hash_type=HashType.MD5)

        hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: change the original value
        new_md5_hash = int.from_bytes(md5_hash.encode(), byteorder='big') - 1
        new_md5_hash = hex(new_md5_hash)[2:]

        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=new_md5_hash,
                                              hash_type=HashType.MD5)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=md5_hash,
                                              hash_type=HashType.SHA256)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=md5_hash,
                                              hash_type=HashType.SHA512)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # TEST: sha256 hash
        sha256_hash = sha256(SINGLE_ISO_PATH)

        hash_validator = HashSumValidator(hash_sum=sha256_hash,
                                          hash_type=HashType.SHA256)

        hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: change the original value
        new_sha256_hash = int.from_bytes(sha256_hash.encode(),
                                         byteorder='big') - 1
        new_sha256_hash = hex(new_sha256_hash)[2:]

        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=new_sha256_hash,
                                              hash_type=HashType.SHA256)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=sha256_hash,
                                              hash_type=HashType.MD5)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=sha256_hash,
                                              hash_type=HashType.SHA512)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # TEST: sha512 hash
        sha512_hash = sha512(SINGLE_ISO_PATH)

        hash_validator = HashSumValidator(hash_sum=sha512_hash,
                                          hash_type=HashType.SHA512)

        hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: change the original value
        new_sha512_hash = int.from_bytes(sha512_hash.encode(),
                                         byteorder='big') - 1
        new_sha512_hash = hex(new_sha512_hash)[2:]

        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=new_sha512_hash,
                                              hash_type=HashType.SHA512)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=sha512_hash,
                                              hash_type=HashType.MD5)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))

        # Negative case: use another hash algorithms
        with pytest.raises(ValidationError):
            hash_validator = HashSumValidator(hash_sum=sha512_hash,
                                              hash_type=HashType.SHA256)
            hash_validator.validate(pathlib.Path(SINGLE_ISO_PATH))


def test_release_info_validator():
    # Positive case: RELEASE.INFO data is well-formed
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: yaml.safe_load(RELEASE_INFO)}):

        ReleaseInfoValidator().validate(
            pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: NAME field is missed
    _release_info = yaml.safe_load(RELEASE_INFO)
    _release_info.pop('NAME')
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        with pytest.raises(ValidationError):
            ReleaseInfoValidator().validate(
                pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: VERSION is missed
    _release_info = yaml.safe_load(RELEASE_INFO)
    _release_info.pop('VERSION')
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        with pytest.raises(ValidationError):
            ReleaseInfoValidator().validate(
                pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: BUILD is missed
    _release_info = yaml.safe_load(RELEASE_INFO)
    _release_info.pop('BUILD')
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        with pytest.raises(ValidationError):
            ReleaseInfoValidator().validate(
                pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: OS is missed
    _release_info = yaml.safe_load(RELEASE_INFO)
    _release_info.pop('OS')
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        with pytest.raises(ValidationError):
            ReleaseInfoValidator().validate(
                pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: COMPONENTS is missed
    _release_info = yaml.safe_load(RELEASE_INFO)
    _release_info.pop('COMPONENTS')
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        with pytest.raises(ValidationError):
            ReleaseInfoValidator().validate(
                pathlib.Path('/path/to/RELEASE_INFO'))

    # Negative case: incorrect fields values
    _release_info = yaml.safe_load(RELEASE_INFO)
    with patch.object(pathlib.Path, 'exists', new=lambda x: True), \
            patch.object(pathlib.Path, 'is_file', new=lambda x: True), \
            patch(CONTENT_LOADER_IMPORT_PATH, new_callable=PropertyMock,
                  return_value={ContentType.YAML:
                                    lambda x: _release_info}):

        # NAME field
        _original = _release_info['NAME']

        for name in (1, ["abc"], {"abc": 1}):
            _release_info['VERSION'] = name
            with pytest.raises(ValueError):
                ReleaseInfoValidator().validate(
                    pathlib.Path('/path/to/RELEASE_INFO'))

        _release_info['NAME'] = _original

        # VERSION field
        _original = _release_info['VERSION']

        for version in (1, 1.2, '1', '1.', '1.1', '1.1.', '1..1', '1..1.1',
                        'a.b.c', 'abc', [1, 2, 3], {1: {1: {2}}}):
            _release_info['VERSION'] = version
            with pytest.raises(ValueError):
                ReleaseInfoValidator().validate(
                    pathlib.Path('/path/to/RELEASE_INFO'))

        _release_info['VERSION'] = _original

        # BUILD field
        _original = _release_info['BUILD']

        for build in (1.2, '1.', '1.1', '1..1', 'a', 'abc', [1], {1: 2}):
            _release_info['VERSION'] = build
            with pytest.raises(ValueError):
                ReleaseInfoValidator().validate(
                    pathlib.Path('/path/to/RELEASE_INFO'))

        _release_info['BUILD'] = _original

        # OS field
        _original = _release_info['BUILD']

        for build in (1, 1.2, [1], {1: 2}):
            _release_info['VERSION'] = build
            with pytest.raises(ValueError):
                ReleaseInfoValidator().validate(
                    pathlib.Path('/path/to/RELEASE_INFO'))

        _release_info['BUILD'] = _original

        # COMPONENTS field
        _original = _release_info['BUILD']

        for build in (1, 1.2, 'abc', {1: 2}):
            _release_info['VERSION'] = build
            with pytest.raises(ValueError):
                ReleaseInfoValidator().validate(
                    pathlib.Path('/path/to/RELEASE_INFO'))

        _release_info['BUILD'] = _original
