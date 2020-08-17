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
