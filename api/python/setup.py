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
    ], # TODO
    keywords='Provisioner API',
    packages=packages,  # TODO use if needed find_packages
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
        'salt==3000.3',  # FIXME 2019.2.0 is buggy, TODO update salt packages for provisioner setup rpm as well
        'attrs'
    ],  # TODO
    setup_requires=['pytest-runner'],
    extras_require={
        'test': tests_require
    },
    tests_require=tests_require
)
