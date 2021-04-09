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
from pathlib import Path

import attr

from . import defs


logger = logging.getLogger(__name__)


JobsCmdArgs = attr.make_class(
    'JobsCmdArgs', (
        'action',
        'ini_file',
        'jjb_args',
    )
)


def manage_jobs(cmd_args):
    # do not import that at module level to avoid too early
    # logging initialization that happens in JJB itself
    # pylint: disable=import-outside-toplevel
    from jenkins_jobs.cli.entry import JenkinsJobs

    cmd_args.action = defs.JobsActionT(cmd_args.action)

    if cmd_args.action == defs.JobsActionT.CONFIG_DUMP:
        return Path(defs.JOBS_CONFIG_EXAMPLE).read_text()

    # defs.JobsActionT.UPDATE or defs.JobsActionT.DELETE
    argv = [
        '--conf', str(cmd_args.ini_file),
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
