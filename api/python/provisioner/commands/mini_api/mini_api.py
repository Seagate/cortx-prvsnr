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

from pathlib import Path
import logging
import argparse

from typing import Type, Union, Dict, Optional, List, Tuple, Any
from jinja2 import Environment, FileSystemLoader
from abc import ABC, abstractmethod
from shlex import quote

from provisioner.vendor import attr
from provisioner import utils, inputs, config
from provisioner.attr_gen import attr_ib
from provisioner.salt import function_run

from provisioner.commands._basic import (
    CommandParserFillerMixin,
    RunArgs
)

logger = logging.getLogger(__name__)


MINI_API_SPEC_HOOK_FIELDS = tuple(
    [f.value for f in config.MiniAPISpecHookFields]
)


class HookSpec(ABC):

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Return whether the hook should be called or not."""

    @property
    def spec(self, normalize=False) -> Any:
        """Return for the hook's spec ."""


@attr.s(auto_attribs=True)
class HookSpecCmd(HookSpec):
    cmd: Optional[str] = None
    args: Optional[Union[str, List[str], Tuple[str]]] = None
    when: Optional[bool] = None
    defaults: Optional['HookSpec'] = None

    def __attrs_post_init__(self):
        if self.args is None:
            self.args = []
        elif isinstance(self.args, str):
            self.args = [self.args]
        elif isinstance(self.args, (list, tuple)):
            self.args = tuple(self.args)
        else:
            raise TypeError(
                f"Unexpected 'args' type: {type(self.args)}"
            )

        # FIXME hard-coded
        if self.defaults:
            for field in config.MiniAPISpecHookFields:
                if getattr(self, field.value) is None:
                    setattr(
                        self, field.value, getattr(self.defaults, field.value)
                    )

        self.when = bool(self.when)

    @property
    def is_active(self) -> bool:
        return self.cmd and self.when

    def spec(self, normalize=False) -> Optional[Any]:
        if normalize:
            if self.is_active:
                cmd = self.cmd.split() + [quote(a) for a in self.args]
                return ' '.join(cmd).strip()
            else:
                return None
        else:
            return attr.asdict(
                self,
                filter=lambda _attr, value: (
                    _attr.name in MINI_API_SPEC_HOOK_FIELDS
                )
            )


@attr.s(auto_attribs=True)
class HookSpecSupportBundle(HookSpec):

    files: Optional[List[Union[Path, str]]] = None

    def __attrs_post_init__(self):
        # TODO converter and validator
        if self.files is None:
            self.files = []
        else:
            self.files = [Path(str(p)) for p in self.files]

    @property
    def is_active(self) -> bool:
        return bool(self.files)

    def spec(self, normalize=False) -> Any:
        return self.files


@attr.s(auto_attribs=True)
class SpecRenderer(CommandParserFillerMixin):
    description = (
        "A helper to render a provisioner mini spec template."
    )

    spec: Union[Path, str] = attr_ib(
        'path_exists', cli_spec='mini_api/spec'
    )
    flow: Union[config.CortxFlows, str] = attr_ib(
        cli_spec='mini_api/flow',
        validator=attr.validators.in_(config.CortxFlows),
        converter=config.CortxFlows
    )
    level: Union[config.MiniAPILevels, str] = attr_ib(
        cli_spec='mini_api/level',
        validator=attr.validators.in_(config.MiniAPILevels),
        converter=config.MiniAPILevels
    )
    confstore: str = attr_ib(
        cli_spec='mini_api/confstore', default='""'
    )
    normalize: bool = attr_ib(
        cli_spec='mini_api/normalize',
        default=False
    )

    @property
    def default_defaults(self):
        return dict(when=(self.level == config.MiniAPILevels.NODE))

    @property
    def render_ctx(self):
        return dict(
            flow=self.flow.value,
            level=self.level.value,
            # TODO document it is available in the context
            confstore=self.confstore
        )

    def _parse_hook(
        self,
        hook: str,
        hook_spec: Union[Dict, List],
        defaults: Optional[HookSpec] = None
    ) -> Tuple[HookSpec, Dict]:
        try:
            hook = config.MiniAPIHooks(hook)
        except ValueError:
            logger.warning(f"Unexpected hook '{hook}', ignoring")
            return HookSpecCmd(), {}

        # case: shorthand for 'hook: cmd'
        if isinstance(hook_spec, str):
            hook_spec = dict(cmd=hook_spec)
        elif not (hook_spec is None or isinstance(hook_spec, dict)):
            raise TypeError(
                f"a dictionary is expected for hook '{hook.value}',"
                f" provided {type(hook_spec)}"
            )

        _hook_spec = {
            f.value: hook_spec[f.value]
            for f in config.MiniAPISpecHookFields
            if f.value in hook_spec
        }
        main_spec = HookSpecCmd(defaults=defaults, **_hook_spec)

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
                event_spec = {
                    config.MiniAPISpecHookFields.CMD.value: event_spec
                }

            if isinstance(event_spec, bool):
                event_spec = (
                    main_spec.spec(normalize=False) if event_spec else None
                )

            # it should be dict or None now
            events[config.event_name(hook, event)] = (
                HookSpecCmd() if event_spec is None else HookSpecCmd(
                    defaults=main_spec, **event_spec
                )
            )

        return main_spec, events

    def render(self):
        jinja_env = Environment(
            loader=FileSystemLoader(str(self.spec.parent)),
            autoescape=True
        )
        template = jinja_env.get_template(self.spec.name)
        res = template.render(**self.render_ctx)
        # TODO deprecate that, legacy way of templating
        return res.replace("$URL", self.confstore)

    def _build_spec(self, sw_spec: Dict):
        defaults = HookSpecCmd(
            **sw_spec.pop(
                config.MiniAPISpecFields.DEFAULTS.value,
                self.default_defaults
            )
        )

        res = {
            config.MiniAPISpecFields.DEFAULTS.value: {
                config.MiniAPISpecHookFields.WHEN.value: True
            }
        }

        events = {}
        for hook, hook_spec in list(sw_spec.items()):
            _hook_spec, _events = self._parse_hook(
                hook, hook_spec, defaults=defaults
            )
            if _hook_spec.is_active or not self.normalize:
                res[hook] = _hook_spec.spec(normalize=self.normalize)
            events.update({
                ev: spec.spec(normalize=self.normalize)
                for ev, spec in _events.items() if spec.is_active
            })

        res[config.MiniAPISpecFields.EVENTS.value] = (
            sw_spec.pop(config.MiniAPISpecFields.EVENTS.value, {})
        )
        res[config.MiniAPISpecFields.EVENTS.value].update(events)

        return res

    def build(self):
        res = {}

        # render the template as a very first step
        config_str = self.render()
        # deserialize
        config_spec = utils.load_yaml_str(config_str)
        # verify that different rendering results are not mixed here
        ctx = config_spec.pop(
            config.MiniAPISpecFields.CTX.value, None
        )
        if ctx and (ctx != self.render_ctx):
            raise ValueError(
                f"the spec is already rendered for a different context: {ctx}"
            )

        support_bundle = config_spec.pop(
            config.MiniAPISpecFields.SUPPORT_BUNDLE.value, None
        )
        if support_bundle:
            support_bundle = HookSpecSupportBundle(support_bundle)

        # format validation: single top level key
        if len(config_spec) != 1:
            raise ValueError(
                "multiple components on the top level:"
                f" {list(config_spec)}"
            )

        sw, sw_spec = next(iter(config_spec.items()))

        # format validation: top level value is a dict
        if not isinstance(sw_spec, dict):
            raise TypeError(
                "a dictionary is expected as a top level value,"
                f" provided {type(sw_spec)}"
            )

        # store the rendered ctx
        res[config.MiniAPISpecFields.CTX.value] = self.render_ctx
        # restore support bundle data
        if support_bundle:
            res[config.MiniAPISpecFields.SUPPORT_BUNDLE.value] = (
                support_bundle.spec(normalize=self.normalize)
            )
        # store the sw spec
        res[sw] = self._build_spec(sw_spec)

        return res

    #     config_str = self.render()

    #    if self.normalize:
    #        config_str = utils.dump_yaml_str(dict(component=sw_spec))

    def run(self):
        return utils.dump_yaml_str(self.build())

        # TODO EOS-20788 POC how to set env
        # import subprocess, os
        # my_env = os.environ.copy()
        # my_env["PATH"] = "/usr/sbin:/sbin:" + my_env["PATH"]

        # set the env
        # prvsnr_mini_env = dict(PRVSNR_MINI_LEVEL=level, ...)
        # env = os.environ.copy()
        # env.update(prvsnr_mini_env)


@attr.s(auto_attribs=True)
class EventRaiser(CommandParserFillerMixin):
    description = (
        "A mini API helper to call hooks and raise events."
    )

    event: str = attr_ib(
        cli_spec='mini_api/event',
        validator=attr.validators.in_(config.MINI_API_EVENT_NAMES)
    )
    flow: Union[config.CortxFlows, str] = attr_ib(
        cli_spec='mini_api/flow',
        validator=attr.validators.in_(config.CortxFlows),
        converter=config.CortxFlows
    )
    level: Union[config.MiniAPILevels, str] = attr_ib(
        cli_spec='mini_api/level',
        validator=attr.validators.in_(config.MiniAPILevels),
        converter=config.MiniAPILevels
    )
    fail_fast: bool = attr_ib(
        cli_spec='mini_api/fail_fast',
        default=False
    )
    targets: str = RunArgs.targets

    def run(self):
        return function_run(
            'setup_conf.raise_event',
            fun_kwargs=dict(
                event=self.event,
                flow=self.flow.value,
                level=self.level.value
            ),
            targets=self.targets
        )


@attr.s(auto_attribs=True)
class MiniAPI(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    mini_api_list = {
        'render_spec': SpecRenderer,
        'raise_event': EventRaiser
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
