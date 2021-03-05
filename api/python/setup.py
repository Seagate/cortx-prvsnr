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

import os
import sys

from setuptools import setup, find_packages

# TODO check python version

try:
    here = os.path.abspath(os.path.dirname(__file__))
except NameError:
    # it can be the case when we are being run as script or frozen
    here = os.path.abspath(os.path.dirname(sys.argv[0]))

metadata = {'__file__': os.path.join(here, 'provisioner', '__metadata__.py')}
with open(metadata['__file__'], 'r') as f:
    exec(f.read(), metadata)

tests_require = [
    'pytest==5.1.1',
    'testinfra==3.1.0',
    'docker==4.0.2',
    'flake8==3.7.8',
    'pytest-xdist==1.29.0',
    'pytest-timeout==1.3.4',
    'pytest-mock==3.1.0',
]

codacy_requrie = [
    'bandit==1.7.0',
    'prospector==1.3.1',
    'pylint==2.5.3',
    'radon==4.3.2'
]


# requiring pytest-runner only when pytest is invoked
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

packages = ['provisioner']

setup(
    name=metadata['__title__'],
    version=metadata['__version__'],
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    maintainer=metadata['__maintainer__'],
    maintainer_email=metadata['__maintainer_email__'],
    url=metadata['__url__'],
    description=metadata['__description__'],
    long_description=metadata['__long_description__'],
    download_url=metadata['__download_url__'],
    license=metadata['__license__'],
    classifiers=[
        "Programming Language :: Python :: 3.6"  # TODO test and declare others
    ],  # TODO
    keywords='Provisioner API',
    packages=find_packages(
        exclude=['test', 'test.*', 'docs', 'docs*', 'simulation']
    ),
    package_dir={'provisioner': 'provisioner'},
    # TODO LICENSE, other
    # package_data={
    #    'provisioner': [
    #        'api_spec.yaml',
    #        'params_spec.yaml',
    #        'provisioner.conf'
    #    ]
    # },
    include_package_data=True,
    # zip_safe=False,  TODO,
    entry_points={
        'console_scripts': [
            'provisioner = provisioner.__main__:main',
        ],
    },
    install_requires=[
        'PyYAML',
        'salt == 3002.2'
    ],  # TODO
    setup_requires=([] + pytest_runner),
    extras_require={
        'test': tests_require,
        'codacy': codacy_requrie,
    },
    tests_require=tests_require
)
