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

from . import __metadata__ as meta

SCRIPT_DIR = Path(__file__).resolve().parent

JENKINS_URL_DEFAULT = 'http://localhost:8080/'

CWD = Path.cwd()

CTX_DIR = CWD / f".{meta.__title__}"

CREDS_FILE_DEFAULT = CWD / 'jenkins.credentials'

###############
# SERVER      #
###############

SERVER_DIR = SCRIPT_DIR / 'server'
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
    SERVER_JENKINS_CONFIG_TMPL
)

SERVER_VOLUME_NAME = 'jenkins_home'
SERVER_JENKINS_HOME = '/var/jenkins_home'

SERVER_INPUTS = CWD / 'jenkins.properties'
SERVER_JENKINS_CONFIG = SERVER_DIR / 'jenkins.yaml'


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
JOBS_CONFIG_EXAMPLE = JOBS_DIR / 'jenkins.ini.example'

JOBS_CTX_DIR = CTX_DIR / 'jobs'
JOBS_CONFIG = CWD / 'jenkins.jobs.ini'

##############


DOCKER_SOCKET = Path('/var/run/docker.sock')

SERVER_CONTAINER_NAME = 'cortx-prvsnr-jenkins'

LOGGING_FORMAT = '%(asctime)s - %(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d]: %(message)s'  # noqa: E501
LOGLEVEL_DEFAULT = 'WARNING'
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
    CONFIG_DUMP = "config-dump"
