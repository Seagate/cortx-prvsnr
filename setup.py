#!/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import os
import glob
from fnmatch import fnmatch
from setuptools import setup
import json

def get_version() ->str:
    """ returns version string """
    if os.path.isfile("./VERSION"):
        with open("VERSION") as v:
            return v.read().strip()
    return "2.0.0"


def get_license() -> str:
    """ Returns license information """
    with open('LICENSE', 'r') as lf:
        return lf.read()

def get_description() -> str:
    """ Returns description """
    with open('README.md', 'r') as rf:
        long_description = rf.read()

def get_install_requirements() -> list:
    """ Returns pre-requisite """

    with open('requirements.txt') as req:
        install_requires = [line.strip() for line in req]
    try:
        with open('requirements.ext.txt') as req:
            install_requires = install_requires + [line.strip() for line in req]
    except Exception:
        pass
    return install_requires

def get_conf_files() -> list:
    """ returns list of conf files """

    return glob.glob('conf/*.yaml*')

def get_requirements_files() -> list:
    """ Returns requirements file """

    if os.path.exists('requirements.txt'):
      return ['requirements.txt']
    return []

def get_secret_files() -> list:
    """Returns secret files"""
    return glob.glob('conf/secret/*')

setup(name='cortx-provisioner',
    version=get_version(),
    url='https://github.com/Seagate/cortx-provisioner',
    license='Seagate',
    author='CORTX Dev',
    author_email='cortx@seagate.com',
    description='CORTX Provisioner',
    package_dir={'cortx': 'src'},
    packages=[
        'cortx.provisioner', 'cortx.setup'
    ],
    package_data={
        'cortx': ['py.typed']
    },
    entry_points={
        'console_scripts': [
            'cortx_setup = cortx.setup.cortx_setup:main'
        ]
    },
    data_files=[
        ('/opt/seagate/cortx/provisioner/conf', get_conf_files()),
        ('/opt/seagate/cortx/provisioner/conf', get_requirements_files()),
        ('/etc/cortx/solution/secret/', get_secret_files()),
        ('/opt/seagate/cortx/provisioner/bin', ['src/setup/cortx_deploy'])
    ],
    long_description=get_description(),
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=get_install_requirements()
)
