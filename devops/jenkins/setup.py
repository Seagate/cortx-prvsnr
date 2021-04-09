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

PACKAGE = 'cortx_jenkins'
PACKAGE_DIR = PACKAGE
TOOL = PACKAGE.replace('_', '-')


try:
    here = os.path.abspath(os.path.dirname(__file__))
except NameError:
    # it can be the case when we are being run as script or frozen
    here = os.path.abspath(os.path.dirname(sys.argv[0]))

metadata = {'__file__': os.path.join(here, PACKAGE_DIR, '__metadata__.py')}
with open(metadata['__file__'], 'r') as f:
    exec(f.read(), metadata)

install_requires = [
    'python-jenkins==1.7.0',
    'requests==2.25.1',
    'attrs==20.3.0',
    'docker==5.0.0',
    'jenkins-job-builder==3.9.0'
]

tests_require = [
    # 'pytest==5.1.1',
    'flake8'
]

codacy_requires = [
    'bandit==1.7.0',
    'prospector==1.3.1',
    'pylint==2.5.3',
    'radon==4.3.2'
]


# requiring pytest-runner only when pytest is invoked
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

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
    keywords='Cortx Provisioner Jenkins Server Agent Jobs',
    packages=find_packages(
        exclude=['test', 'test.*', 'docs', 'docs*', 'simulation']
    ),
    package_dir={PACKAGE_DIR: PACKAGE},
    include_package_data=True,
    # zip_safe=False,  TODO,
    entry_points={
        'console_scripts': [
            f"{TOOL} = {PACKAGE}.__main__:main",
        ],
    },
    install_requires=install_requires,
    setup_requires=([] + pytest_runner),
    extras_require={
        'test': tests_require,
        'codacy': codacy_requires,
    },
    tests_require=tests_require
)
