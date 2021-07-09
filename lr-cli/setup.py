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


from setuptools import setup, find_packages

setup(
    name='cortx-setup',
    version='2.0.0',
    author='Seagate',
    author_email='support@seagate.com',
    maintainer='Seagate',
    maintainer_email=f'{"maintainer"}',
    url='https://github.com/Seagate/cortx-prvsnr',
    description='cortx_setup API',
    long_description=f'{"description"}',
    download_url=f'{"url"}',
    license='Seagate',
    classifiers=[
        "Programming Language :: Python :: 3.6"
    ],
    keywords='cortx_setup API',
    packages=find_packages(),
    package_dir={'cortx_setup': 'cortx_setup'},
    include_package_data=True,
    entry_points={
        'console_scripts': ['cortx_setup=cortx_setup.main:main'],
    },
    install_requires=[
        'cortx-prvsnr >= 2.0.42'
    ],
)
