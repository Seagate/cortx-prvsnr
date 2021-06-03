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

from typing import Type, Union, Dict, Optional, List
from pathlib import Path
import logging
import argparse
from jinja2 import Environment, FileSystemLoader

from provisioner.vendor import attr
from provisioner import utils, inputs, config
from provisioner.attr_gen import attr_ib

from provisioner.commands._basic import (
    CommandParserFillerMixin
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SpecRenderer(CommandParserFillerMixin):
    description = (
        "A helper to render  a provisioner mini spec template."
    )

    spec: Union[Path, str] = attr_ib(
        'path_exists', cli_spec='mini_api/spec'
    )
    flow: Union[Path, str] = attr_ib(
        cli_spec='mini_api/flow',
        validator=attr.validators.in_(config.CortxFlows),
        converter=config.CortxFlows
    )
    level: Union[Path, str] = attr_ib(
        cli_spec='mini_api/level',
        validator=attr.validators.in_(config.MiniAPILevels),
        converter=config.MiniAPILevels
    )
    normalize: bool = attr_ib(
        cli_spec='mini_api/normalize',
        default=False,
    )

    def _normalize_spec(self, spec: Dict, defaults: Optional[Dict] = None):
        res = {}

        if defaults is None:
            defaults = {}

        # FIXME hard-coded
        for field in ('cmd', 'args', 'when'):
            res[field] = spec.get(field, defaults.get(field))

        res['when'] = bool(res['when'])
        return res if res['when'] else None

    def _normalize_hook(
        self, hook: str, hook_spec: Optional[Union[Dict, List]]
    ):
        hook = config.MiniAPIHooks(hook)

        if hook is config.MiniAPIHooks.SUPPORT_BUNDLE:
            if not (hook_spec is None or isinstance(hook_spec, list)):
                raise TypeError(
                    "an array of paths is expected for hook {hook.value},"
                    f" provided {type(hook_spec)}"
                )
            return hook_spec

        if not (hook_spec is None or isinstance(hook_spec, dict)):
            raise TypeError(
                "a dictionary is expected for hook {hook.value},"
                f" provided {type(hook_spec)}"
            )

        default_when = (self.level == config.MiniAPILevels.NODE)
        main_spec = self._normalize_spec(
            hook_spec, {'when': default_when}
        )
        if main_spec is None:
            main_spec = {}

        events = {}

        # FIXME hard-coded
        for event in config.MiniAPIEvents:
            event_spec = hook_spec.get(event.value)
            if not (
                event_spec is None
                or isinstance(event_spec, (dict, str, bool))
            ):
                raise TypeError(
                    "a dictionary, string, boolean or null are expected for"
                    f" {event.value}' event spec, provided {type(event_spec)}"
                )

            if isinstance(event_spec, str):
                event_spec = {'cmd': event_spec}

            if isinstance(event_spec, bool):
                event_spec = main_spec if event_spec else None

            # it should be dict or None now
            if isinstance(event_spec, dict):
                event_spec = self._normalize_spec(event_spec, main_spec)
            events[event.value] = event_spec

        main_spec['events'] = events
        return main_spec

    def run(self):
        # EOS-20788 POC
        jinja_env = Environment(
            loader=FileSystemLoader(str(self.spec.parent)),
            autoescape=True
        )
        template = jinja_env.get_template(self.spec.name)
        ctx = dict(flow=self.flow.value, level=self.level.value)

        config_info_str = template.render(**ctx)

        if self.normalize:
            config = utils.load_yaml_str(config_info_str)
            if len(config) != 1:
                raise ValueError(
                    "multiple components on the top level:"
                    f" {list(config)}"
                )
            _, config = next(iter(config.items()))

            if not isinstance(config, dict):
                raise TypeError(
                    "a dictionary is expected as a second level,"
                    f" provided {type(config)}"
                )

            for hook, hook_spec in list(config.items()):
                config[hook] = self._normalize_hook(hook, hook_spec)

            config_info_str = utils.dump_yaml_str(dict(component=config))

        return config_info_str

        # TODO EOS-20788 POC how to set env
        # import subprocess, os
        # my_env = os.environ.copy()
        # my_env["PATH"] = "/usr/sbin:/sbin:" + my_env["PATH"]

        # set the env
        # prvsnr_mini_env = dict(PRVSNR_MINI_LEVEL=level, ...)
        # env = os.environ.copy()
        # env.update(prvsnr_mini_env)


@attr.s(auto_attribs=True)
class MiniAPI(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    mini_api_list = {
        'render_spec': SpecRenderer
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
