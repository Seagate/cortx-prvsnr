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

from typing import Union, Dict, Optional, List, Tuple, Any
from jinja2 import Environment, FileSystemLoader
from abc import ABC, abstractmethod
from shlex import quote

from provisioner.vendor import attr
from provisioner import utils, config

from provisioner.commands._basic import (
    CommandParserFillerMixin,
)

from .common import MiniAPIParams

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
    spec_version: str = config.MiniAPISpecVersions.INITIAL.value

    def __attrs_post_init__(self):  # noqa: C901
        # FIXME hard-coded
        if self.defaults:
            for field in config.MiniAPISpecHookFields:
                if getattr(self, field.value) is None:
                    setattr(
                        self, field.value, getattr(self.defaults, field.value)
                    )

        if self.cmd is None:
            self.cmd = []
        elif isinstance(self.cmd, str):
            # Note. initial mini spec format didn't bother with
            #       proper arguments definition
            self.cmd = [self.cmd.strip()]
            if self.spec_version == config.MiniAPISpecVersions.INITIAL.value:
                self.cmd = self.cmd[0].split()

        if not isinstance(self.cmd, (list, tuple)):
            raise TypeError(
                f"Unexpected 'cmd' type: {type(self.cmd)}"
            )

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

        # Note. initial mini spec format didn't bother with
        #       proper arguments definition
        if self.spec_version == config.MiniAPISpecVersions.INITIAL.value:
            _args = []
            for _arg in self.args:
                _args.extend(_arg.strip().split())
            self.args = _args

        self.when = bool(self.when)

    @property
    def is_active(self) -> bool:
        return self.cmd and self.when

    def spec(self, normalize=False) -> Optional[Any]:
        if normalize:
            if self.is_active:
                if self.spec_version == config.MiniAPISpecVersions.INITIAL.value:
                    cmd = self.cmd
                    args = self.args
                else:
                    cmd = [quote(a) for a in self.cmd]
                    args = [quote(a) for a in self.args]
                return cmd + args
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

    spec: Union[Path, str] = MiniAPIParams.spec
    flow: Union[config.CortxFlows, str] = MiniAPIParams.flow
    level: Union[config.MiniAPILevels, str] = MiniAPIParams.level
    confstore: str = MiniAPIParams.confstore
    normalize: bool = MiniAPIParams.normalize

    _version: str = attr.ib(init=False, default=None)

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
            hook = config.MiniAPIBaseHooks(hook)
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
        main_spec = HookSpecCmd(
            defaults=defaults, spec_version=self._version, **_hook_spec
        )

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
                    defaults=main_spec,
                    spec_version=self._version,
                    **event_spec
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

        self._version = config_spec.pop(
            config.MiniAPISpecFields.VERSION.value, None
        )

        if self._version is None:
            logger.info("Legacy (initial) version is being parsed")
            self._version = config.MiniAPISpecVersions.INITIAL.value

        support_bundle = config_spec.pop(
            config.MiniAPISpecFields.SUPPORT_BUNDLE.value, None
        )
        if support_bundle:
            support_bundle = HookSpecSupportBundle(support_bundle)

        # format validation: single top level key
        if len(config_spec) != 1:
            logger.warning(
                f"multiple components on the top level of '{self.spec}':"
                f" {list(config_spec)}"
            )

        # mark version
        res[config.MiniAPISpecFields.VERSION.value] = self._version
        # store the rendered ctx
        res[config.MiniAPISpecFields.CTX.value] = self.render_ctx
        # restore support bundle data
        if support_bundle:
            res[config.MiniAPISpecFields.SUPPORT_BUNDLE.value] = (
                support_bundle.spec(normalize=self.normalize)
            )

        for sw, sw_spec in config_spec.items():
            # format validation: top level value is a dict
            if not isinstance(sw_spec, dict):
                raise TypeError(
                    "a dictionary is expected as a top level value,"
                    f" provided {type(sw_spec)}"
                )

            # store the sw spec
            res[sw] = self._build_spec(sw_spec)

        return res

    def run(self):
        return utils.dump_yaml_str(self.build())
