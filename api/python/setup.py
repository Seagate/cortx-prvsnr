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

tests_require = []
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
    keywords='EOS Provisioner API',
    packages=packages,  # TODO use if needed find_packages
    package_dir={'provisioner': 'provisioner'},
    # package_data={'': ['LICENSE']},  # TODO
    # include_package_data=True,  # TODO
    # zip_safe=False,  TODO
    install_requires=[
        'PyYAML',
        'salt==2019.2.0'
    ],  # TODO
    setup_requires=['pytest-runner'],
    extras_require={
        'test': tests_require
    },
    tests_require=tests_require,
    scripts=[]  # TODO
)
