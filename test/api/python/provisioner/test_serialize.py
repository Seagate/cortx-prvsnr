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

import pytest
import json

from provisioner.vendor import attr
from provisioner.serialize import (
    PrvsnrType, dumps, loads, PRVSNR_TYPE_KEY
)
from provisioner import values

from provisioner.errors import (
    ProvisionerError, PrvsnrTypeDecodeError
)


class SomePrvsnrClass1(PrvsnrType):
    def __init__(self, attr1, attr2=2, attr3='123'):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


@attr.s(auto_attribs=True)
class SomePrvsnrClass2(PrvsnrType):
    attr1: str = attr.ib(default=None)
    attr2: str = attr.ib(default='store')
    attr3: str = attr.ib(init=False, default='')

    def to_args(self):
        return (
            None,
            attr.asdict(self, filter=lambda attr, _: attr.name != 'attr3')
        )


def test_decode_wrong_prvsnr_type():
    dct = {"_prvsnr_type_": ["ValueError"], "args": [123]}
    assert loads(json.dumps(dct), strict=False) == dct

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct))

    assert excinfo.value.spec == dct
    assert type(excinfo.value.reason) is ValueError
    assert (
        (
            'value for {} should be an iterable with 2 items'
            .format(PRVSNR_TYPE_KEY)
        ) in str(excinfo.value.reason)
    )


def test_decode_unknown_module():
    dct = {"_prvsnr_type_": ["__somemodule__", "ValueError"], "args": [123]}
    assert loads(json.dumps(dct), strict=False) == dct

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct))

    assert excinfo.value.spec == dct
    assert type(excinfo.value.reason) is ModuleNotFoundError
    assert "No module named '__somemodule__'" in str(excinfo.value.reason)


def test_decode_unknown_cls():
    dct = {"_prvsnr_type_": ["builtins", "SomeClass"], "args": [123]}
    assert loads(json.dumps(dct), strict=False) == dct

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct))

    assert excinfo.value.spec == dct
    assert type(excinfo.value.reason) is AttributeError
    assert (
        "module 'builtins' has no attribute 'SomeClass'"
        in str(excinfo.value.reason)
    )


def test_decode_cls_with_wrong_args():
    # missed attr1
    dct1 = {
        "_prvsnr_type_": [
            'test.api.python.provisioner.test_serialize', "SomePrvsnrClass1"
        ]
    }
    assert loads(json.dumps(dct1), strict=False) == dct1

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct1))
    assert excinfo.value.spec == dct1
    assert type(excinfo.value.reason) is TypeError
    assert (
        "__init__() missing 1 required positional argument: 'attr1'"
        in str(excinfo.value.reason)
    )

    # missed attr1
    dct2 = {
        "_prvsnr_type_": [
            'test.api.python.provisioner.test_serialize', "SomePrvsnrClass1"
        ], "kwargs": {"attr2": "1.2.3"}
    }
    assert loads(json.dumps(dct2), strict=False) == dct2

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct2))
    assert excinfo.value.spec == dct2
    assert type(excinfo.value.reason) is TypeError
    assert (
        "__init__() missing 1 required positional argument: 'attr1'"
        in str(excinfo.value.reason)
    )

    # unknown attr4
    dct3 = {
        "_prvsnr_type_": [
            'test.api.python.provisioner.test_serialize', "SomePrvsnrClass1"
        ], "kwargs": {"attr4": "1.2.3"}
    }
    assert loads(json.dumps(dct3), strict=False) == dct3

    with pytest.raises(PrvsnrTypeDecodeError) as excinfo:
        loads(json.dumps(dct3))
    assert excinfo.value.spec == dct3
    assert type(excinfo.value.reason) is TypeError
    assert (
        "__init__() got an unexpected keyword argument 'attr4'"
        in str(excinfo.value.reason)
    )


def test_serialize_simple():
    obj1 = SomePrvsnrClass1(3, 4)
    obj1_json = dumps(obj1)
    obj2 = loads(obj1_json)
    assert obj1 == obj2


def test_serialize_attr_cls():
    obj1 = SomePrvsnrClass2(3, 4)
    obj1_json = dumps(obj1)
    obj2 = loads(obj1_json)
    assert obj1 == obj2


def test_special_values_serialization():
    for value in values._values.values():
        _json = dumps(value)
        value2 = loads(_json)
        assert value2 is value


def test_serialize_builtins_exception():
    exc1 = ValueError(123)
    exc2 = loads(dumps({'exc': exc1}))['exc']
    assert type(exc1) is type(exc2)
    assert exc1.args == exc2.args


def test_serialize_prvsnr_exception():
    exc1 = ProvisionerError(123)
    exc2 = loads(dumps({'exc': exc1}))['exc']
    assert type(exc1) is type(exc2)
    assert exc1.args == exc2.args
