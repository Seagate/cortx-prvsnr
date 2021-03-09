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


import sys
from typing import Dict, Union
from copy import deepcopy

import logging
import logging.config
import logging.handlers

from .vendor import attr
from . import inputs
from .errors import LogMsgTooLong
from .base import prvsnr_config
from .config import (
    LOG_NULL_HANDLER as NULL_HANDLER,
    LOG_CONSOLE_HANDLER as CONSOLE_HANDLER,
    LOG_FILE_HANDLER as LOGFILE_HANDLER,
    LOG_FILE_SALT_HANDLER as SALTLOGFILE_HANDLER,
    LOG_CMD_FILTER as CMD_FILTER,
    LOG_HUMAN_FORMATTER,
    LOG_TRUNC_MSG_TMPL,
    LOG_TRUNC_MSG_SIZE_MAX
)

logger = logging.getLogger(__name__)


class CommandFilter(logging.Filter):
    def __init__(self, cmd: str = None):
        self._cmd = cmd

    @property
    def cmd(self):
        return self._cmd

    @cmd.setter
    def cmd(self, cmd: str):
        self._cmd = cmd

    def filter(self, record):
        record.prvsnrcmd = self._cmd
        return True


class LogFileFilter(logging.Filter):
    def filter(self, record):
        return not(record.name.startswith("salt.")
                   and (record.levelno < logging.INFO))


class SaltLogFileFilter(logging.Filter):
    def filter(self, record):
        return record.name.startswith("salt.")


class NoTraceExceptionFormatter(logging.Formatter):
    def format(self, record):
        # ensure cache won't be used for exception formatting
        # and formatException would be called later
        record.exc_text = ''
        return super().format(record)

    def formatException(self, exc_info):
        # TODO IMPROVE check docs for exc_info
        return repr(getattr(exc_info[1], 'reason', exc_info[1]))


class NoErrorSysLogHandler(logging.handlers.SysLogHandler):
    def emit(self, record):
        try:
            super().emit(record)
        except LogMsgTooLong:
            _msg = record.getMessage()
            # we don't need any further format operations since a msg
            # is already formatted
            record.args = tuple()
            _len = LOG_TRUNC_MSG_SIZE_MAX
            # Note.
            #   as part of EOS-15450 it was encountered that the following loop
            #   may lead to 0 _len, likely it happened due to glitch in
            #   underlying logging engines (rsyslog likely),
            #   so try to log until _len is reasonably long
            #   to avoid infinite loop
            # TODO IMPROVE
            #      if we were not able to log anythin need
            #      to (try) register that fact somewhere anyway
            while _len > len(LOG_TRUNC_MSG_TMPL):
                record.msg = LOG_TRUNC_MSG_TMPL.format(_msg[:_len])
                try:
                    super().emit(record)
                except LogMsgTooLong:
                    _len = _len // 2
                else:
                    break

    def handleError(self, record):
        t, v, _ = sys.exc_info()
        if issubclass(t, OSError) and 'Message too long' in str(v):
            raise LogMsgTooLong()
        else:
            super().handleError(record)


def build_log_args_cls(log_config=None):  # noqa: C901 FIXME
    if log_config is None:
        log_config = prvsnr_config.logging

    def _log_attr_name(hname, aname):
        return '{}_{}'.format(hname, aname)

    def build_handler_cls(hname, hattrs, log_config):

        @attr.s(auto_attribs=True)
        class _NullLogHandler:
            pass

        @attr.s(auto_attribs=True)
        class _LogHandler:
            if 'level' in hattrs:
                level: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': "{} log level".format(hname),
                            'choices': ['DEBUG', 'INFO', 'WARN', 'ERROR']
                        }
                    }, default=hattrs['level']
                )

            if ('formatter' in hattrs) and ('formatters' in log_config):
                formatter: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': "{} log records format".format(hname),
                            'choices': list(log_config['formatters'])
                        }
                    }, default=hattrs['formatter']
                )

        if hname == NULL_HANDLER:
            return _NullLogHandler
        elif hname == CONSOLE_HANDLER:
            @attr.s(auto_attribs=True)
            class _ConsoleStreamLogHandler(_LogHandler):
                stream: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': f"{CONSOLE_HANDLER} log stream",
                            'choices': ['stderr', 'stdout']
                        }
                    },
                    default=hattrs['stream'][-6:],
                    converter=(lambda stream: 'ext://sys.{}'.format(stream))
                )
            return _ConsoleStreamLogHandler
        elif hname in (LOGFILE_HANDLER, SALTLOGFILE_HANDLER):
            @attr.s(auto_attribs=True)
            class _FileLogHandler(_LogHandler):
                filename: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': f"{hname} handler file path",
                            'metavar': 'FILE'
                        }
                    },
                    default=hattrs['filename']
                )
                maxBytes: int = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': (
                                f"{hname} handler "
                                "max file size in bytes"
                            ),
                            'metavar': 'BYTES',
                            'type': int
                        }
                    },
                    default=hattrs['maxBytes'],
                    converter=int
                )
                backupCount: int = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': (
                                f"{hname} handler "
                                "max backup files number"
                            ),
                            'metavar': 'NUMBER',
                            'type': int
                        }
                    },
                    default=hattrs['backupCount'],
                    converter=int
                )
            return _FileLogHandler
        else:
            return _LogHandler

    log_attrs = {
        'hcls': {}
    }

    if isinstance(log_config.get('filters', {}).get(CMD_FILTER), dict):
        log_attrs.update({
            'cmd': attr.ib(
                type=str,
                default=log_config['filters'][CMD_FILTER].get(
                    'cmd', 'unknown'
                ),
                converter=(lambda cmd: cmd if cmd else 'unknown')
            )
        })

    for hname, hattrs in log_config['handlers'].items():
        # args for switching handler on/off
        # Note. null handler is not dynamically configurable
        log_attrs.update({
            hname: attr.ib(
                init=(hname != NULL_HANDLER),
                type=bool,
                default=(hname in log_config['root']['handlers']),
                metadata=(None if hname == NULL_HANDLER else {
                    inputs.METADATA_ARGPARSER: {
                        'help': "{} logging handler".format(hname),
                        'action': 'store_bool'
                    }
                })
            )
        })
        hcls = build_handler_cls(hname, hattrs, log_config)
        log_attrs['hcls'][hname] = hcls

        # args for handlers attributes prefixed with handler names
        for hcls_attr_name, hcls_attr in attr.fields_dict(hcls).items():
            if inputs.METADATA_ARGPARSER in hcls_attr.metadata:
                # TODO IMPROVE use some attr api to copy spec
                log_attrs[_log_attr_name(hname, hcls_attr_name)] = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: hcls_attr.metadata[
                            inputs.METADATA_ARGPARSER
                        ]
                    },
                    type=hcls_attr.type,
                    default=hcls_attr.default
                )

    log_attrs['hcls'] = attr.ib(
        init=False, type=Dict, default=log_attrs['hcls']
    )
    log_attrs['handlers'] = attr.ib(
        init=False, type=Dict, default=attr.Factory(dict)
    )

    @attr.s(auto_attribs=True, these=log_attrs)
    class _LogArgs:
        # TODO IMPROVE use some readonly dict/cls
        _log_config = deepcopy(log_config)

        def __attrs_post_init__(self):
            self.update_handlers()

        def update_handlers(self):
            _dict = attr.asdict(self)
            # set handler attributes with stripped handler name prefixes
            for hname, hcls in list(self.hcls.items()):
                hattrs = {}
                for fname, fattr in attr.fields_dict(hcls).items():
                    laname = _log_attr_name(hname, fname)
                    if laname in _dict:
                        hattrs[fname] = _dict[laname]
                self.handlers[hname] = hcls(**hattrs)

        @classmethod
        def original_config(cls):
            return deepcopy(cls._log_config)

        def config(self):
            res = self.original_config()

            root_handlers = []
            human_handlers = []
            for hname, hattrs in res['handlers'].items():
                if getattr(self, hname, False):
                    if hattrs.get('formatter') == LOG_HUMAN_FORMATTER:
                        human_handlers.append(hname)
                    else:
                        root_handlers.append(hname)
                    handler = self.handlers[hname]
                    for fname, fvalue in attr.asdict(handler).items():
                        hattrs[fname] = fvalue
            # adjust active handlers
            res['root']['handlers'][:] = root_handlers + human_handlers

            if hasattr(self, 'cmd'):
                res['filters'][CMD_FILTER]['cmd'] = self.cmd

            return res

        @classmethod
        def fill_parser(cls, parser):
            inputs.ParserFiller.fill_parser(cls, parser)

    return _LogArgs


LogArgs = build_log_args_cls()


def reset_logging():
    for handler in logging.root.handlers[:]:
        handler.flush()
        logging.root.removeHandler(handler)
        handler.close()


def set_logging(log_args: Union[LogArgs, None] = None):
    reset_logging()
    logging.config.dictConfig(
        prvsnr_config.logging if log_args is None else log_args.config()
    )
