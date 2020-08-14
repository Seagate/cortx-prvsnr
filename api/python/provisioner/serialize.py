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

import json
import functools
from typing import Any
from importlib import import_module

from .errors import PrvsnrTypeDecodeError


PRVSNR_TYPE_ATTR = '_prvsnr_type_'
TO_ARGS_METHOD = 'to_args'
FROM_ARGS_METHOD = 'from_args'

PRVSNR_TYPE_KEY = PRVSNR_TYPE_ATTR
PRVSNR_ARGS_KEY = 'args'
PRVSNR_KWARGS_KEY = 'kwargs'


class PrvsnrType:
    _prvsnr_type_ = True

    def to_args(self) -> Any:
        return self.to_args_default(self)

    @staticmethod
    def to_args_default(obj) -> Any:
        if (
            isinstance(obj, BaseException) and
            not hasattr(obj, PRVSNR_TYPE_ATTR)
        ):
            return ((obj.args), None)
        else:
            return (None, obj.__dict__)

    @classmethod
    def from_args(cls, *args, **kwargs) -> 'PrvsnrType':
        return cls.from_args_default(cls, *args, **kwargs)

    @staticmethod
    def from_args_default(cls, *args, **kwargs) -> Any:
        return cls(*args, **kwargs)


# TODO DOC works on for classes defined in the top level of a module
# TODO explore how pickle iplements similar logic
#      https://docs.python.org/3.6/library/pickle.html#what-can-be-pickled-and-unpickled
class PrvsnrJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, PRVSNR_TYPE_ATTR) or isinstance(obj, BaseException):
            try:
                cls = type(obj)
                res = {PRVSNR_TYPE_KEY: [cls.__module__, cls.__name__]}

                if hasattr(obj, PRVSNR_TYPE_ATTR):
                    args, kwargs = getattr(
                        obj, TO_ARGS_METHOD,
                        functools.partial(PrvsnrType.to_args_default, obj)
                    )()
                else:  # BaseException
                    args, kwargs = PrvsnrType.to_args_default(obj)

                if args:
                    res[PRVSNR_ARGS_KEY] = args
                if kwargs:
                    res[PRVSNR_KWARGS_KEY] = kwargs
            # it is expected that encoder's 'default' method
            # should either return an encodeable representation of an
            # object or raise a TypeError
            # https://docs.python.org/3.6/library/json.html#basic-usage
            except Exception as exc:
                raise TypeError(
                    'Failed to encode object {}: error {}'
                    .format(obj, exc)
                )
            else:
                return res

        return super().default(obj)


def json_prvsnr_type_hook(dct, strict=True):
    prvsnr_type = dct.get(PRVSNR_TYPE_KEY, None)
    if prvsnr_type:
        try:
            try:
                m_name, cls_name = prvsnr_type
            except ValueError:
                raise ValueError(
                    'value for {} should be an iterable with 2 items,'
                    ' provided: {}'
                    .format(PRVSNR_TYPE_KEY, prvsnr_type)
                )

            module = import_module(m_name)
            cls = getattr(module, cls_name)
            args = dct.get(PRVSNR_ARGS_KEY, ())
            kwargs = dct.get(PRVSNR_KWARGS_KEY, {})
            return getattr(
                cls, FROM_ARGS_METHOD,
                functools.partial(PrvsnrType.from_args_default, cls)
            )(*args, **kwargs)
        except Exception as exc:
            if strict:
                raise PrvsnrTypeDecodeError(dct, exc)
    return dct


def loads(s, strict=True, *args, **kwargs):
    kwargs['object_hook'] = functools.partial(
        json_prvsnr_type_hook, strict=strict
    )
    return json.loads(s, *args, **kwargs)


def dumps(obj, *args, **kwargs):
    kwargs['cls'] = PrvsnrJSONEncoder
    return json.dumps(obj, **kwargs)
