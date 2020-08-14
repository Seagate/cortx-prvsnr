#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#



from typing import Dict, Union
from copy import deepcopy

import logging
import logging.config

from .vendor import attr
from . import inputs
from .base import prvsnr_config
from .config import (
    LOG_NULL_HANDLER as null_handler,
    LOG_CONSOLE_HANDLER as console_handler,
    LOG_FILE_HANDLER as logfile_handler,
    LOG_CMD_FILTER as cmd_filter,
    LOG_HUMAN_FORMATTER
)

logger = logging.getLogger(__name__)


# TODO TEST EOS-7495
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


# TODO TEST EOS-7495
class NoTraceExceptionFormatter(logging.Formatter):
    def format(self, record):
        # ensure cache won't be used for exception formatting
        # and formatException would be called later
        record.exc_text = ''
        return super().format(record)

    def formatException(self, exc_info):
        # TODO IMPROVE check docs for exc_info
        return repr(getattr(exc_info[1], 'reason', exc_info[1]))


def build_log_args_cls(log_config=None):
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

        if hname == null_handler:
            return _NullLogHandler
        elif hname == console_handler:
            @attr.s(auto_attribs=True)
            class _ConsoleStreamLogHandler(_LogHandler):
                stream: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': f"{console_handler} log stream",
                            'choices': ['stderr', 'stdout']
                        }
                    },
                    default=hattrs['stream'][-6:],
                    converter=(lambda stream: 'ext://sys.{}'.format(stream))
                )
            return _ConsoleStreamLogHandler
        elif hname == logfile_handler:
            @attr.s(auto_attribs=True)
            class _FileLogHandler(_LogHandler):
                filename: str = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': f"{logfile_handler} handler file path",
                            'metavar': 'FILE'
                        }
                    },
                    default=hattrs['filename']
                )
                maxBytes: int = attr.ib(
                    metadata={
                        inputs.METADATA_ARGPARSER: {
                            'help': (
                                f"{logfile_handler} handler "
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
                                f"{logfile_handler} handler "
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

    if type(log_config.get('filters', {}).get(cmd_filter)) is dict:
        log_attrs.update({
            'cmd': attr.ib(
                type=str,
                default=log_config['filters'][cmd_filter].get(
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
                init=(hname != null_handler),
                type=bool,
                default=(hname in log_config['root']['handlers']),
                metadata=(None if hname == null_handler else {
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
                res['filters'][cmd_filter]['cmd'] = self.cmd

            return res

        @classmethod
        def fill_parser(cls, parser):
            inputs.ParserFiller.fill_parser(cls, parser)

    return _LogArgs


LogArgs = build_log_args_cls()


# TODO TEST EOS-7495
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
