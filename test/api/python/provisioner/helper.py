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

from functools import partial
from typing import Callable, Any, Tuple, Dict
from provisioner.vendor import attr

# TODO consider to use mocks (e.g. pytest-mock plugin)


@attr.s(auto_attribs=True)
class MockRes:
    key: str
    res: Any
    args: Tuple
    kwargs: Dict

    @property
    def args_all(self):
        return (self.args, self.kwargs)


def mock_fun(mock, *args, mock_res=None, mock_key=None, **kwargs):
    try:
        if isinstance(mock, Exception):
            raise mock
        else:
            res = (
                mock(*args, **kwargs) if isinstance(mock, Callable)
                else mock
            )
    except Exception as exc:
        res = exc

    if isinstance(mock_res, list):
        if mock_key is None:
            mock_key = mock
        mock_res.append(MockRes(mock_key, res, args, kwargs))

    if isinstance(res, Exception):
        raise res
    else:
        return res


def mock_fun_echo(mock_res=None, mock_key=None):
    return partial(
        mock_fun,
        lambda *args, **kwags: (args, kwags),
        mock_res=mock_res,
        mock_key=mock_key
    )


def mock_fun_result(res, mock_res=None, mock_key=None):
    return partial(mock_fun, res, mock_res=mock_res, mock_key=mock_key)
