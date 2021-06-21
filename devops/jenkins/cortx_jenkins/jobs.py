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

import logging
import configparser
from typing import Dict

import attr

from . import defs, utils


logger = logging.getLogger(__name__)


JobsCmdArgs = attr.make_class(
    'JobsCmdArgs', (
        'config',
        'action',
        'jjb_args'
    )
)


def gen_jobs_ini(config: Dict):
    jobs_config = config[defs.ConfigSectionT.JOBS.value]
    global_config = config[defs.ConfigSectionT.GLOBAL.value]

    if not jobs_config['jenkins'].get('user'):
        jobs_config['jenkins']['user'] = global_config['username']

    if not jobs_config['jenkins'].get('password'):
        jobs_config['jenkins']['password'] = global_config['token']

    if not jobs_config['jenkins'].get('url'):
        jobs_config['jenkins']['url'] = global_config['url']

    _config = configparser.ConfigParser()
    _config.optionxform = lambda option: option
    for section in jobs_config:
        _config.add_section(section)
        for k, v in jobs_config[section].items():
            _config.set(section, k, str(v))

    with open(defs.JOBS_CONFIG, 'w') as fh:
        _config.write(fh)


def manage_jobs(cmd_args: JobsCmdArgs):
    # do not import that at module level to avoid too early
    # logging initialization that happens in JJB itself
    # pylint: disable=import-outside-toplevel
    from jenkins_jobs.cli.entry import JenkinsJobs

    cmd_args.action = defs.JobsActionT(cmd_args.action)

    gen_jobs_ini(cmd_args.config)

    utils.set_ssl_verify(
        cmd_args.config[defs.ConfigSectionT.GLOBAL.value]['ssl_verify']
    )

    # defs.JobsActionT.UPDATE or defs.JobsActionT.DELETE
    argv = [
        '--conf', str(defs.JOBS_CONFIG),
        '-l', logging.getLevelName(logger.getEffectiveLevel()),
        cmd_args.action.value,
        '--recursive'
    ]

    if cmd_args.jjb_args:
        # TODO 'split' might be too naive in some cases
        argv.extend(cmd_args.jjb_args.split())

    argv.append(str(defs.JOBS_DIR))

    logger.debug(f"Calling JJB with the following args: {argv}")
    return JenkinsJobs(argv).execute()
