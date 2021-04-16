#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
#

import os
import re
from enum import Enum
from pathlib import Path

from . import __title__

SCRIPT_DIR = Path(__file__).resolve().parent

CWD = Path.cwd()

PKGNAME = __title__
CTX_DIR = CWD / f".{PKGNAME}"

CREDS_FILE_DEFAULT = CWD / 'jenkins.credentials'
CONFIG_FILE_EXAMPLE = SCRIPT_DIR / 'cortx-jenkins.toml.example'
CONFIG_FILE = CWD / 'cortx-jenkins.toml'


class ConfigSectionT(Enum):
    """Jenkins config sections"""
    GLOBAL = "global"
    SERVER = "server"
    AGENT = "agent"
    JOBS = "jobs"


#####################
# SERVER & SMEE.IO  #
#####################

SERVER_DIR = SCRIPT_DIR / 'server'

#  SMEE.IO
SMEEIO_IMAGE_VERSION = '0.0.1'
SMEEIO_IMAGE_NAME = 'seagate/cortx-prvsnr-jenkins-smeeio'
SMEEIO_IMAGE_TAG = SMEEIO_IMAGE_VERSION
SMEEIO_IMAGE_NAME_FULL = f"{SMEEIO_IMAGE_NAME}:{SMEEIO_IMAGE_VERSION}"
SMEEIO_DOCKERFILE = SERVER_DIR / 'Dockerfile.smee.io'
SMEEIO_CONTAINER_NAME = 'cortx-prvsnr-jenkins-smeeio'


SERVER_CTX_DIR = CTX_DIR / 'server'

SERVER_IMAGE_VERSION = '0.0.1'
SERVER_IMAGE_NAME = 'seagate/cortx-prvsnr-jenkins'
SERVER_IMAGE_TAG = SERVER_IMAGE_VERSION
SERVER_IMAGE_NAME_FULL = f"{SERVER_IMAGE_NAME}:{SERVER_IMAGE_VERSION}"

SERVER_CONTAINER_NAME = 'cortx-prvsnr-jenkins'
SERVER_DOCKERFILE = SERVER_DIR / 'Dockerfile.jenkins'
SERVER_DOCKER_CTX_DIR = SERVER_DIR
SERVER_PLUGINS_LIST = SERVER_DIR / 'plugins.txt'
SERVER_JENKINS_CONFIG_TMPL = SERVER_DIR / 'jenkins.yaml.tmpl'

SERVER_DOCKER_CTX_LIST = (
    SERVER_DOCKERFILE,
    SERVER_PLUGINS_LIST,
    SERVER_JENKINS_CONFIG_TMPL,
    SMEEIO_DOCKERFILE
)

SERVER_VOLUME_NAME = 'jenkins_home'
SERVER_JENKINS_HOME = '/var/jenkins_home'

SERVER_PROPERTIES_NAME = 'jenkins.properties'
SERVER_JENKINS_CONFIG = SERVER_DIR / 'jenkins.yaml'

SERVER_HTTPS_CERT_NAME = 'cert.pem'
SERVER_HTTPS_PK_NAME = 'key.pem'
SERVER_HTTPS_RSA_NAME = 'key.rsa.pem'


###############
#  AGENT     #
##############

AGENT_DIR = SCRIPT_DIR / 'agent'
AGENT_CTX_DIR = CTX_DIR / 'agent'

AGENT_CONTAINER_NAME = 'cortx-prvsnr-jenkins-agent'
AGENT_DOCKERFILE = AGENT_DIR / 'Dockerfile.inbound-agent'
AGENT_DOCKER_CTX_LIST = (
    AGENT_DOCKERFILE,
    AGENT_DIR / 'setup_docker.sh'
)
AGENT_DOCKER_CTX_DIR = AGENT_DIR

AGENT_IMAGE_VERSION = '0.0.1'
AGENT_IMAGE_NAME = 'seagate/cortx-prvsnr-jenkins-inbound-agent'
AGENT_IMAGE_TAG = AGENT_IMAGE_VERSION
AGENT_IMAGE_NAME_FULL = f"{AGENT_IMAGE_NAME}:{AGENT_IMAGE_VERSION}"

AGENT_WORK_DIR_DEFAULT = '/var/lib/jenkins'

MASTER_AGENT = 'master'

EXPECTED_AGENT_LABELS = set(['cortx-prvsnr-ci'])

AGENT_CONFIG_REGEX = re.compile(
    r'.*<application-desc main-class="hudson.remoting.jnlp.Main"><argument>'
    r'([a-z0-9]*).*<argument>-workDir<\/argument><argument>([^<]*).*'
)


###############
#  JOBS       #
###############

JOBS_DIR = SCRIPT_DIR / 'jobs'

JOBS_CTX_DIR = CTX_DIR / 'jobs'
JOBS_CONFIG = CWD / 'jenkins.jobs.ini'


##############


DOCKER_SOCKET = Path('/var/run/docker.sock')

SERVER_CONTAINER_NAME = 'cortx-prvsnr-jenkins'

LOGGING_FORMAT = '%(asctime)s - %(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d]: %(message)s'  # noqa: E501
LOGLEVEL_DEFAULT = 'INFO'
LOGLEVEL = os.getenv('LOGLEVEL', LOGLEVEL_DEFAULT).upper()

LOCALHOST = 'localhost'


class AgentActionT(Enum):

    """Jenkins agent actions"""
    CREATE = "create"
    STOP = "stop"
    START = "start"
    RESTART = "restart"
    REMOVE = "remove"


ServerActionT = AgentActionT


class JobsActionT(Enum):

    """Jenkins agent actions"""
    UPDATE = "update"
    DELETE = "delete"
