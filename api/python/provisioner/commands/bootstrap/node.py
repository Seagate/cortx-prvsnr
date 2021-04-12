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
# Module with Node and Node Grains setup


import logging
from typing import (
    Dict,
    Iterable,
    List,
    Optional
)
from provisioner.vendor import attr

logger = logging.getLogger(__name__)


# TODO IMPROVE EOS-8473 converters and validators
@attr.s(auto_attribs=True)
class NodeGrains:
    fqdn: str = None
    host: str = None
    ipv4: List = attr.Factory(list)
    fqdns: List = attr.Factory(list)
    not_used: Dict = attr.Factory(dict)

    @classmethod
    def from_grains(cls, **kwargs):
        # Assumption: 'not_used' doesn't appear in grains
        not_used = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k not in attr.fields_dict(cls)
        }
        return cls(**kwargs, not_used=not_used)

    @property
    def addrs(self):
        res = []
        for _attr in ('host', 'fqdn', 'fqdns', 'ipv4'):
            v = getattr(self, _attr)
            if v:
                if type(v) is list:
                    res.extend(v)
                else:  # str is expected
                    res.append(v)
        return list(set(res))


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class Node:
    minion_id: str
    host: str
    user: str = 'root'
    port: int = 22

    grains: Optional[NodeGrains] = None
    # ordered by priority
    _ping_addrs: List = attr.Factory(list)

    @classmethod
    def from_spec(cls, spec: str) -> 'Node':
        kwargs = {}

        parts = spec.split(':')
        kwargs['minion_id'] = parts[0]
        hostspec = parts[1]

        try:
            kwargs['port'] = parts[2]
        except IndexError:
            pass

        parts = hostspec.split('@')
        try:
            kwargs['user'] = parts[0]
            kwargs['host'] = parts[1]
        except IndexError:
            del kwargs['user']
            kwargs['host'] = parts[0]

        return cls(**kwargs)

    def __str__(self):  # noqa: D105
        """Information of Node in Cortx cluster."""
        return (
            '{}:{}@{}:{}'
            .format(
                self.minion_id,
                self.user,
                self.host,
                self.port
            )
        )

    @property
    def addrs(self):
        return list(set([self.host] + self.grains.addrs))

    @property
    def ping_addrs(self):
        return self._ping_addrs

    @ping_addrs.setter
    def ping_addrs(self, addrs: Iterable):
        # TODO IMPROVE EOS-8473 more effective way to order
        #      w.g. use dict (it remembers the order) and set intersection
        priorities = [
            self.grains.fqdn
        ] + self.grains.fqdns + [
            self.host,
            self.grains.host
        ] + self.grains.ipv4

        self._ping_addrs[:] = []
        for addr in priorities:
            if addr in addrs and (addr not in self._ping_addrs):
                self._ping_addrs.append(addr)

        for addr in addrs:
            if addr not in self._ping_addrs:
                self._ping_addrs.append(addr)
