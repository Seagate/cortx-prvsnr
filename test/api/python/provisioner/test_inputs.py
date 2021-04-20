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

import pytest
from unittest.mock import call
import argparse
from typing import Union, List
from pathlib import Path
import functools

from provisioner.vendor import attr
from provisioner.errors import SWUpdateRepoSourceError
from provisioner import values
from provisioner.values import UNCHANGED
from provisioner import inputs
from provisioner.param import (
    Param, ParamDictItem
)
from provisioner.inputs import (
    METADATA_PARAM_GROUP_KEY,
    METADATA_ARGPARSER,
    AttrParserArgs,
    InputAttrParserArgs,
    PillarKeysList,
    PillarInputBase,
    ParamsList,
    ParamGroupInputBase,
    NTP, Network, NetworkParams,
    ParamDictItemInputBase,
    SWUpdateRepo,
    ParserFiller
)
from provisioner.pillar import PillarKey
from provisioner.api_spec import param_spec as _param_spec


# HELPERS and FIXTURES

test_param_spec = {
    'some_param_gr/attr1': Param(
        'some_param_gr/attr1', ('some-pi-key1', 'some-pi-path1')
    ),
    'some_param_gr/attr2': Param(
        'some_param_gr/attr2', ('some-pi-key2', 'some-pi-path2')
    ),
    'some/dict/item1': ParamDictItem(
        'some/dict/item1', ('some-pi-key3', 'some-pi-path3'),
        'some_key_attr', 'some_value_attr'
    )
}


@attr.s(auto_attribs=True)
class SomeParamGroup(ParamGroupInputBase):
    _param_group = 'some_param_gr'
    attr1: str = ParamGroupInputBase._attr_ib(_param_group)
    attr2: int = ParamGroupInputBase._attr_ib(_param_group, default=1)


@attr.s(auto_attribs=True)
class SomeParamDictItem(ParamDictItemInputBase):
    _param_di = test_param_spec['some/dict/item1']
    some_key_attr: str = ParamDictItemInputBase._attr_ib(
        is_key=True, descr='some_key_attr descr'
    )
    some_value_attr: str = ParamDictItemInputBase._attr_ib(
        descr='some_value_attr descr'
    )


@pytest.fixture(scope="module")
def param_spec():
    return test_param_spec


@pytest.fixture
def param_spec_mocked(monkeypatch, param_spec):
    monkeypatch.setattr(
        inputs, 'param_spec', param_spec
    )
    return param_spec


# AttrParserArgs tests


def test_inputs_AttrParserArgs_kwargs_keys_by_default():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help', 'type'))


def test_attr_parser_args_kwargs_keys_with_choices():
    SC = attr.make_class("SC", {
        "x": attr.ib(type=str, default='123', metadata={
            METADATA_ARGPARSER: dict(choices='somechoices')
        })
    })
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help', 'type', 'choices'))


def test_attr_parser_args_kwargs_keys_with_dest():
    SC = attr.make_class("SC", {
        "x": attr.ib(type=str, default='123', metadata={
            METADATA_ARGPARSER: dict(dest='somedest')
        })
    })
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help', 'type', 'dest'))


def test_attr_parser_args_kwargs_keys_with_const():
    SC = attr.make_class("SC", {
        "x": attr.ib(type=str, default='123', metadata={
            METADATA_ARGPARSER: dict(const='someconst')
        })
    })
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help', 'type', 'const'))


def test_attr_parser_args_kwargs_keys_for_boolean():
    SC = attr.make_class("SC", {"x": attr.ib(type=bool, default=False)})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'help'))


def test_attr_parser_args_kwargs_keys_for_store_false():
    SC = attr.make_class("SC", {"x": attr.ib(type=int, metadata={
        METADATA_ARGPARSER: dict(action='store_false')
    })})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'help'))


def test_attr_parser_args_kwargs_keys_for_store_const():
    SC = attr.make_class("SC", {"x": attr.ib(type=int, metadata={
        METADATA_ARGPARSER: dict(action='store_const')
    })})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help'))


def test_attr_parser_args_name_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x).name == '--x'


def test_inputs_AttrParserArgs_name_for_optional_with_underscore():
    SC = attr.make_class("SC", {"x_y": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x_y).name == '--x-y'


def test_inputs_AttrParserArgs_name_for_positional():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).name == 'x'


def test_inputs_AttrParserArgs_action_by_default():
    SC = attr.make_class("SC", {"x": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x).action == 'store'


def test_inputs_AttrParserArgs_action_for_boolean():
    SC = attr.make_class("SC", {"x": attr.ib(default=None, type=bool)})
    assert AttrParserArgs(attr.fields(SC).x).action == 'store_true'


def test_attr_parser_args_action_specified():
    SC = attr.make_class("SC", {"x": attr.ib(default=None, metadata={
        METADATA_ARGPARSER: dict(action='someaction')
    })})
    assert AttrParserArgs(attr.fields(SC).x).action == 'someaction'


def test_attr_parser_args_default_set():
    SC = attr.make_class("SC", {"x": attr.ib(default=123)})
    assert AttrParserArgs(attr.fields(SC).x).name == '--x'
    assert AttrParserArgs(attr.fields(SC).x).default == 123


def test_inputs_AttrParserArgs_default_not_set():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).name == 'x'
    assert AttrParserArgs(attr.fields(SC).x).default is None


def test_inputs_AttrParserArgs_type_default():
    SC = attr.make_class("SC", {"x": attr.ib()})
    attr_parser_type = AttrParserArgs(attr.fields(SC).x).type
    assert type(attr_parser_type) is functools.partial
    assert attr_parser_type.func == AttrParserArgs.value_from_str
    assert attr_parser_type.args == ()
    assert attr_parser_type.keywords == dict(v_type=attr.fields(SC).x.type)


def test_inputs_AttrParserArgs_type_custom():
    def some_fun(value):
        pass

    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'type': some_fun
                },
            },
            default='123'
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).type == some_fun


def test_inputs_AttrParserArgs_no_metavar_for_positional():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).metavar is None


def test_inputs_AttrParserArgs_metavar_by_default_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert AttrParserArgs(attr.fields(SC).x).metavar == 'STR'


def test_inputs_AttrParserArgs_metavar_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'metavar': 'SOME-METAVAR'
                },
            },
            default='123'
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).metavar == 'SOME-METAVAR'


def test_inputs_AttrParserArgs_help_by_default_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert AttrParserArgs(attr.fields(SC).x).help == ''


def test_inputs_AttrParserArgs_help_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'help': 'some help'
                },
            }
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).help == 'some help'


def test_attr_parser_args_dest_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'dest': 'somedest'
                },
            }
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).dest == 'somedest'


def test_attr_parser_args_const_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'const': 'someconst'
                },
            }
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).const == 'someconst'


def test_attr_parser_args_value_from_str():
    assert AttrParserArgs.value_from_str('PRVSNR_NONE') is None
    assert AttrParserArgs.value_from_str(
        '["1", "2", "3"]', v_type=List
    ) == ['1', '2', '3']
    assert AttrParserArgs.value_from_str(
        '["1", "2", "3"]', v_type='json'
    ) == ['1', '2', '3']
    assert AttrParserArgs.value_from_str(
         '{"1": 2}', v_type='json'
    ) == {'1': 2}


def test_InputAttrParserArgs_value_from_str():
    assert InputAttrParserArgs.value_from_str('PRVSNR_NONE') == UNCHANGED


# ### PillarKeysList ###

def test_inputs_PillarKeysList_len():
    assert len(PillarKeysList()) == 0
    assert len(PillarKeysList([PillarKey('1'), PillarKey('2')])) == 2


def test_inputs_PillarKeysList_iter():
    pi_keys = [PillarKey('1'), PillarKey('2')]
    pi_keys_list = PillarKeysList(pi_keys)
    assert pi_keys == list(pi_keys_list)


def test_inputs_PillarKeysList_from_args():
    PillarKeysList.from_args('1', ('2', '3')) == PillarKeysList(
        [PillarKey('1'), PillarKey('2', '3')]
    )
    with pytest.raises(TypeError):
        PillarKeysList.from_args(['1', '2'])


def test_inputs_PillarKeysList_fill_parser(param_spec_mocked):
    parser = argparse.ArgumentParser()
    PillarKeysList.fill_parser(parser)
    args = parser.parse_args([])
    assert args.args == []

    args = parser.parse_args(
        '123 456'.split()
    )
    assert args.args == ['123', '456']


# ### PillarInputBase ###

# TODO IMPROVE more checks for attrs
def test_inputs_PillarInputBase_attrs():
    fdict = attr.fields_dict(PillarInputBase)
    type_fun = fdict['value'].metadata[METADATA_ARGPARSER]['type']
    # TODO IMPROVE use mocks to verify that
    #      value_from_str is called with v_type='json'
    assert type_fun('123') == 123
    assert type_fun('{"1" : 23}') == {'1': 23}


def test_inputs_PillarInputBase_from_args():
    keypath = '1/2/3'
    value = 567
    fpath = '890.sls'
    test = PillarInputBase.from_args(
        keypath, value, fpath=fpath
    )
    assert test.keypath == keypath
    assert test.value == value
    assert test.fpath == fpath

    assert PillarInputBase.from_args(
        keypath, value
    ).fpath is None


def test_inputs_PillarInputBase_iter(param_spec_mocked):
    keypath = '1/2/3'
    value = 567
    fpath = '890.sls'
    test = PillarInputBase.from_args(
        keypath, value, fpath=fpath
    )
    assert test.pillar_items() == (
        (PillarKey(keypath, fpath), value),
    )


# TODO IMPROVE more cases
def test_inputs_PillarInputBase_fill_parser(param_spec_mocked):
    parser = argparse.ArgumentParser()
    PillarInputBase.fill_parser(parser)

    args = parser.parse_args(
        '123 456 --fpath 789.sls'.split()
    )
    assert args.keypath == '123'
    assert args.value == 456
    assert args.fpath == '789.sls'

    args = parser.parse_args(
        '123 456'.split()
    )
    assert args.keypath == '123'
    assert args.value == 456
    assert args.fpath is None

    args = parser.parse_args(
        '123 456 --fpath=PRVSNR_NONE'.split()
    )
    assert args.keypath == '123'
    assert args.value == 456
    assert args.fpath is None

    args = parser.parse_args(
        ['123', '[4, 5, 6]']
    )
    assert args.keypath == '123'
    assert args.value == [4, 5, 6]
    assert args.fpath is None

    args = parser.parse_args(
        ['123', '{"4": {"5": 6}}']
    )
    assert args.keypath == '123'
    assert args.value == {"4": {"5": 6}}
    assert args.fpath is None


# ### ParamsList ###

def test_inputs_ParamsList_from_args(param_spec_mocked):
    params = [
        param_spec_mocked['some_param_gr/attr2'],
        Param(
            param_spec_mocked['some/dict/item1'].name / 'key1',
            ('some-pi-key3/key1', 'some-pi-path3')
        )
    ]
    assert ParamsList.from_args(*[str(p) for p in params]).params == params
    assert ParamsList.from_args(*[p for p in params]).params == params
    assert ParamsList.from_args(
        *[str(p) for p in params],
        *[p for p in params]
    ).params == params + params


def test_inputs_ParamsList_iter(param_spec_mocked):
    params = ParamsList.from_args(
        'some_param_gr/attr1', 'some/dict/item1/some-key'
    )
    assert [p for p in params] == params.params


# ### ParamGroupInputBase ###


def test_inputs_ParamGroupInputBase_attr_ib():
    attr1 = attr.fields(SomeParamGroup).attr1
    assert attr1.type is str
    assert attr1.default is UNCHANGED
    assert attr1.metadata[METADATA_PARAM_GROUP_KEY] == 'some_param_gr'

    attr2 = attr.fields(SomeParamGroup).attr2
    assert attr2.type is int
    assert attr2.default == 1
    assert attr2.metadata[METADATA_PARAM_GROUP_KEY] == 'some_param_gr'


def test_inputs_ParamGroupInputBase_from_args():
    test = SomeParamGroup.from_args(attr1='1234', attr2=5)
    assert test.attr1 == '1234'
    assert test.attr2 == 5


def test_inputs_ParamGroupInputBase_param_spec(param_spec_mocked):
    SomeParamGroup.param_spec('attr1') is param_spec_mocked[
        'some_param_gr/attr1'
    ]
    SomeParamGroup.param_spec('attr2') is param_spec_mocked[
        'some_param_gr/attr2'
    ]


def test_inputs_ParamGroupInputBase_iter(param_spec_mocked):
    test = SomeParamGroup('123', 45)
    for param, value in test.pillar_items():
        assert param is param_spec_mocked[str(param.name)]
        assert value == getattr(test, param.name.leaf)


# TODO IMPROVE more cases
def test_inputs_ParamGroupInputBase_fill_parser(param_spec_mocked):
    parser = argparse.ArgumentParser()
    SomeParamGroup.fill_parser(parser)
    args = parser.parse_args(
        '--attr1 PRVSNR_NONE --attr2 PRVSNR_UNCHANGED'.split()
    )
    assert args.attr1 == UNCHANGED
    assert args.attr2 == UNCHANGED


# ### NTP ###

def test_inputs_NTP():
    assert NTP._param_group == 'ntp'
    for param in _param_spec:
        param = Path(param)
        if str(param.parent) == NTP._param_group:
            fattr = attr.fields_dict(NTP)[param.name]
            assert fattr.type is str
            assert fattr.default is UNCHANGED


# ### Network ###


@pytest.mark.outdated
def test_inputs_NETWORK():
    assert NetworkParams._param_group == 'network'
    for param in _param_spec:
        param = Path(param)
        if str(param.parent) == NetworkParams._param_group:
            fattr = attr.fields_dict(Network)[param.name]
            if param.name in (
                'dns_servers',
                'search_domains',
                'primary_data_network_iface',
                'secondary_data_network_iface'
            ):
                assert fattr.type is List
            else:
                assert fattr.type is str
            assert fattr.default is UNCHANGED


# ParamDictItemInputBase tests


def test_inputs_ParamDictItemInputBaseattr_ib():
    some_key_attr = attr.fields(SomeParamDictItem).some_key_attr
    assert some_key_attr.type is str
    assert some_key_attr.default is attr.NOTHING
    assert some_key_attr.metadata[METADATA_ARGPARSER]['help'] == (
        'some_key_attr descr'
    )

    some_value_attr = attr.fields(SomeParamDictItem).some_value_attr
    assert some_value_attr.type is str
    assert some_value_attr.default == UNCHANGED
    assert some_value_attr.metadata[METADATA_ARGPARSER]['help'] == (
        'some_value_attr descr'
    )


def test_inputs_ParamDictItemInputBasefrom_args():
    test = SomeParamDictItem.from_args(some_key_attr='1234', some_value_attr=5)
    assert test.some_key_attr == '1234'
    assert test.some_value_attr == 5


def test_inputs_ParamDictItemInputBaseparam_spec(param_spec_mocked):
    test = SomeParamDictItem(some_key_attr='1234', some_value_attr=5)
    assert test.param_spec() == Param(
        'some/dict/item1/1234', ('some-pi-key3/1234', 'some-pi-path3')
    )


def test_inputs_ParamDictItemInputBaseiter(param_spec_mocked):
    test = SomeParamDictItem('123', 45)
    _iter = test.pillar_items()
    param, value = next(_iter)
    assert param == test.param_spec()
    assert value == 45
    # only one item
    with pytest.raises(StopIteration):
        next(_iter)


# TODO IMPROVE more cases
def test_inputs_ParamDictItemInputBasefill_parser(param_spec_mocked):
    parser = argparse.ArgumentParser()
    SomeParamDictItem.fill_parser(parser)

    args = parser.parse_args('some-key --some-value-attr PRVSNR_NONE'.split())
    assert args.some_value_attr == UNCHANGED

    args = parser.parse_args(
        'some-key --some-value-attr PRVSNR_UNCHANGED'.split()
    )
    assert args.some_value_attr == UNCHANGED


# ### SWUpdateRepo ###

def test_inputs_SWUpdateRepo_attrs():
    assert SWUpdateRepo._param_di == inputs.param_spec['swupdate/repo']

    fattr = attr.fields_dict(SWUpdateRepo)['release']
    assert fattr.type is str
    assert fattr.default is attr.NOTHING

    fattr = attr.fields_dict(SWUpdateRepo)['source']
    assert fattr.type is Union[str, Path]
    assert fattr.default is UNCHANGED


@pytest.mark.outdated
@pytest.mark.patch_logging([(inputs, ('error',))])
def test_inputs_SWUpdateRepo_source_init(tmpdir_function, patch_logging):
    some_release = '1.2.3'

    # special values
    for source in values._values.values():
        res = SWUpdateRepo(some_release, source=source)
        assert res.source == source

    res = SWUpdateRepo(some_release, source=None)
    assert res.source == UNCHANGED

    # directory
    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()
    for source in (repo_dir, str(repo_dir)):
        res = SWUpdateRepo(some_release, source=source)
        assert res.source == repo_dir

    # iso file
    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()
    for source in (repo_iso, str(repo_iso)):
        res = SWUpdateRepo(some_release, source=source)
        assert res.source == repo_iso

    # other existent file object
    non_iso_file = tmpdir_function / 'repo.file'
    non_iso_file.touch()
    with pytest.raises(SWUpdateRepoSourceError) as excinfo:
        SWUpdateRepo(some_release, source=str(non_iso_file))
    assert excinfo.value.source == str(non_iso_file)
    assert excinfo.value.reason == 'not an iso file'

    # existent object but neither file nor dir
    bad_object = '/dev/null'
    with pytest.raises(SWUpdateRepoSourceError) as excinfo:
        SWUpdateRepo(some_release, source=bad_object)
    assert excinfo.value.source == bad_object
    assert excinfo.value.reason == 'not a file or directory'

    # urls are expected to start with http:// or https://
    for source in ('http://some/http/url', 'https://some/http/url'):
        res = SWUpdateRepo(some_release, source=source)
        assert res.source == source

    # any other cases are treated as invalid
    source = 'some/string'
    with pytest.raises(SWUpdateRepoSourceError) as excinfo:
        res = SWUpdateRepo(some_release, source=source)
    assert excinfo.value.source == source
    assert excinfo.value.reason == 'unexpected type of source'

    # TODO non absolute existent one

    # non canonical absolute path
    res = SWUpdateRepo(some_release, source=(repo_dir / '..' / 'repo.iso'))
    assert res.source == repo_iso


def test_inputs_SWUpdateRepo_pillar_key(tmpdir_function):
    some_release = '1.2.3'

    res = SWUpdateRepo(some_release, source='http://some/http/url')
    assert res.pillar_key == some_release


def test_inputs_SWUpdateRepo_pillar_value(tmpdir_function):
    some_release = '1.2.3'

    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()

    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()

    # special values
    for source in values._values.values():
        res = SWUpdateRepo(some_release, source=source)
        assert res.pillar_value == source

    res = SWUpdateRepo(some_release, source=None)
    assert res.pillar_value == UNCHANGED

    # directory
    res = SWUpdateRepo(some_release, source=repo_dir)
    assert res.pillar_value == 'dir'

    # iso file
    res = SWUpdateRepo(some_release, source=repo_iso)
    assert res.pillar_value == 'iso'

    # urls are expected to start with http:// or https://
    for source in ('http://some/http/url', 'https://some/http/url'):
        res = SWUpdateRepo(some_release, source=source)
        assert res.pillar_value == source


def test_inputs_SWUpdateRepo_is_apis(tmpdir_function):
    some_release = '1.2.3'

    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()

    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()

    res = None

    def _check(*args):
        for api in ('is_special', 'is_local', 'is_remote', 'is_dir', 'is_iso'):
            assert getattr(res, api)() == (api in args)

    # special values
    for source in values._values.values():
        res = SWUpdateRepo(some_release, source=source)
        _check('is_special')

    res = SWUpdateRepo(some_release, source=None)
    _check('is_special')

    # directory
    res = SWUpdateRepo(some_release, source=repo_dir)
    _check('is_local', 'is_dir')

    # iso file
    res = SWUpdateRepo(some_release, source=repo_iso)
    _check('is_local', 'is_iso')

    # urls
    res = SWUpdateRepo(some_release, source='https://some/http/url')
    _check('is_remote')


def test_inputs_copy_attr_verify_attrs():
    some_cls = attr.make_class("some_cls", {
        "some_attr": attr.ib(
            default=123,
            validator=None,
            metadata={
                'metadata_key': 1
            },
            repr=False,
            hash=None,
            init=True,
            type=str,
            converter=None,
            kw_only=True
        )
    })

    read_attr = attr.fields(some_cls).some_attr

    copied_attr = inputs.copy_attr(read_attr)

    assert copied_attr == read_attr


def test_ParserFiller_fill_parser_when_action_is_store_bool():
    parser = argparse.ArgumentParser()
    SC = attr.make_class("SC", {
        "y": attr.ib(
            default=123,
            metadata={
                METADATA_ARGPARSER: {
                    'action': 'store_bool',
                    'help': 'some help'
                }
            },
            type=int
        )
    })
    ParserFiller.fill_parser(SC, parser)
    args = parser.parse_args(['--y', '--noy'])
    assert not args.y

    args = parser.parse_args(['--y'])
    assert args.y

    args = parser.parse_args(['--noy'])
    assert not args.y


def test_ParserFiller_fill_parser_with_no_action_in_metadata():
    parser = argparse.ArgumentParser()
    SC = attr.make_class("SC", {
        "y": attr.ib(
            default=123,
            metadata={
                METADATA_ARGPARSER: {
                    'help': 'some help'
                }
            },
            type=int
        )
    })
    ParserFiller.fill_parser(SC, parser)
    args = parser.parse_args(['--y', 'some-value'])
    assert args.y == 'some-value'


def test_ParserFiller_fill_parser_with_no_metadata_argparser():
    parser = argparse.ArgumentParser()
    SC = attr.make_class("SC", {
        "y": attr.ib(
            default=123,
            type=int
        )
    })
    ParserFiller.fill_parser(SC, parser)

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(['--y', 'some-value'])

    assert excinfo.value.code == 2


def test_ParserFiller_fill_parser_input_checks(mocker):
    parser = argparse.ArgumentParser()
    SC = attr.make_class("SC", {
        "y": attr.ib(
            default=True,
            metadata={
                METADATA_ARGPARSER: {
                    'action': 'store_bool',
                    'help': 'some help'
                }
            },
            type=int
        )
    })
    add_args_m = mocker.patch.object(parser, 'add_argument', autospec=True)
    ParserFiller.fill_parser(SC, parser)
    expected_calls = [call('--y', action='store_const',
                           const=True, default=True, dest='y',
                           help='enable some help',
                           metavar='INT'),
                      call('--noy', action='store_const', const=False,
                           default=False, dest='y', help='disable some help',
                           metavar='INT')]
    add_args_m.assert_has_calls(expected_calls)
    assert add_args_m.call_count == len(expected_calls)


@pytest.mark.outdated
def test_ParserFiller_extract_positional_args_happy_path():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            metadata={
                METADATA_ARGPARSER: {
                    'action': 'store_bool',
                    'help': 'some help'
                }
            },
            type=int
        )
    })
    ret = ParserFiller.extract_positional_args(SC, attr.fields_dict(SC))
    assert ret == ([attr.fields(SC).x], {})


@pytest.mark.outdated
def test_ParserFiller_extract_positional_args_no_metadata_argparser():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=int,
            repr=False,
            init=False
        )
    })
    ret = ParserFiller.extract_positional_args(SC, attr.fields_dict(SC))
    assert ret == ([], attr.fields_dict(SC))


@pytest.mark.outdated
def test_ParserFiller_extract_positional_args_default_is_not_NOTHING():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            default=123,
            metadata={
                METADATA_ARGPARSER: {
                    'help': 'some help'
                }
            },
            type=int
        )
    })
    ret = ParserFiller.extract_positional_args(SC, attr.fields_dict(SC))
    assert ret == ([], attr.fields_dict(SC))
