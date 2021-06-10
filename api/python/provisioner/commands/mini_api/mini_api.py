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

import logging
import argparse

from typing import Type

from provisioner.vendor import attr
from provisioner import inputs

from provisioner.commands._basic import (
    CommandParserFillerMixin,
)

from .spec_renderer import SpecRenderer
from .hook_caller import HookCaller

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class MiniAPI(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    mini_api_list = {
        'render': SpecRenderer,
        'hook': HookCaller
    }

    # XXX DRY copy-paste from Helper command
    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        subparsers = parser.add_subparsers(
            dest='helper',
            title='Various Mini Provisioner API helpers',
            description='valid commands',
            # requried=True # ( sad, but python 3.6 doesn't have that
        )

        for helper_name, helper_t in cls.mini_api_list.items():
            subparser = subparsers.add_parser(
                helper_name, description=helper_t.description,
                help=f"{helper_name} helper help", parents=parents,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            inputs.ParserFiller.fill_parser(helper_t, subparser)

    # XXX DRY copy-paste from Helper command
    @classmethod
    def extract_positional_args(cls, kwargs):
        helper_t = cls.mini_api_list[kwargs.pop('helper')]
        _args = [helper_t]

        args, kwargs = super().extract_positional_args(kwargs)
        _args.extend(args)

        args, kwargs = inputs.ParserFiller.extract_positional_args(
            helper_t, kwargs
        )
        _args.extend(args)

        return _args, kwargs

    @staticmethod
    def run(helper_t, *args, **kwargs):
        helper_kwargs = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(helper_t)
        }

        helper = helper_t(*args, **helper_kwargs)

        return helper.run(**kwargs)
