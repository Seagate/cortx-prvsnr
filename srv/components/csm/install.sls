Install NVM and Nodejs :
  cmd.run:
    - name: sh /opt/seagate/ees-prvsnr/srv/components/csm/files/nvm_node_install.sh

Install common runtime libraries:
  pkg.installed:
    - pkgs:
      - python36-pip
      - python36-devel
      - python36-setuptools
      - openssl-devel
      - libffi-devel
      - gcc


Install python packages:
  pip.installed:
    - names:
      - aiohttp
      - paramiko
      - toml
      - PyYAML
      - configparser
      - argparse
      - dict2xml
      - prettytable
      - pika
      - idna
      - jsonschema


Install csm package:
  pkg.installed:
    - name: csm

Install eos-csm package:
  pkg.installed:
    - name: eos-csm

