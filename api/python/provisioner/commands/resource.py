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

from typing import Type
import logging
import argparse
from collections import defaultdict
from copy import deepcopy

from ..vendor import attr
from .. import inputs

from ._basic import (
    RunArgsRemote,
    RunArgsSaltClient,
    CommandParserFillerMixin
)

from provisioner.scm.saltstack.rc_sls.base import SLSResourceManager


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class Resource(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = [RunArgsRemote, RunArgsSaltClient]

    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        # add common args block for all resources
        resource_parser_common = argparse.ArgumentParser(add_help=False)
        super().fill_parser(resource_parser_common)
        parents.append(resource_parser_common)

        subparsers = parser.add_subparsers(
            dest='resource_name',
            title='resources',
            description='valid resources'
        )

        rc_manager = SLSResourceManager()
        rc_states = defaultdict(list)

        for state_t in rc_manager.transitions:
            rc_states[state_t.resource_t].append(state_t)

        for rc_t, state_ts in rc_states.items():
            rc_name = rc_t.resource_t_id.value
            rc_subparser = subparsers.add_parser(
                rc_name, description=f"{rc_name} configuration",
                help=f"{rc_name} resource help", parents=parents,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

            state_subparsers = rc_subparser.add_subparsers(
                dest="resource_state_name",
                title=f"resource {rc_name} states",
                description=f"valid states for resource {rc_name}"
            )

            for state_t in state_ts:
                state_name = state_t.name
                state_subparser = state_subparsers.add_parser(
                    state_name, description=f"{state_name} configuration",
                    help=f"{state_name} configuration help", parents=parents,
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter
                )
                inputs.ParserFiller.fill_parser(state_t, state_subparser)

    @classmethod
    def extract_positional_args(cls, kwargs):
        # FIXME
        rc_manager = SLSResourceManager()
        state_ts = {st_t.name: st_t for st_t in rc_manager.transitions}

        # XXX ??? FIXME
        kwargs.pop('resource_name')

        state_name = kwargs.pop('resource_state_name')
        state_t = state_ts[state_name]
        _args = [state_t]

        args, kwargs = super().extract_positional_args(kwargs)
        _args.extend(args)

        args, kwargs = inputs.ParserFiller.extract_positional_args(
            state_t, kwargs
        )
        _args.extend(args)

        return _args, kwargs

    @staticmethod
    def run(state_t, *args, **kwargs):
        _kwargs = deepcopy(kwargs)

        salt_args = RunArgsSaltClient(**{
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSaltClient)
        })

        run_args = RunArgsRemote(**{
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsRemote)
        })

        if run_args.runner_minion_id:
            return salt_args.salt_client.provisioner_cmd(
                'resource',
                fun_args=([state_t.name] + list(args)),
                fun_kwargs=_kwargs,
                runner_minion_id=run_args.runner_minion_id
            )
        else:
            rc_manager = SLSResourceManager()
            state = state_t(*args, **kwargs)
            return rc_manager.run(
                state,
                trans_kwargs=dict(client=salt_args.client),
                targets=run_args.targets
            )
