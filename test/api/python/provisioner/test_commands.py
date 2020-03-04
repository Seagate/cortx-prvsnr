import pytest
import attr

from provisioner import (
    commands, inputs, ALL_MINIONS
)
from provisioner.salt import State
from provisioner.values import MISSED


def test_get_from_spec(monkeypatch):
    get_cmd = commands.Get.from_spec()
    assert get_cmd.params_type is inputs.ParamsList

    class ParamsListChild(inputs.ParamsList):
        pass

    monkeypatch.setattr(
        inputs, 'ParamsListChild', ParamsListChild, raising=False
    )

    get_cmd = commands.Get.from_spec(params_type='ParamsListChild')
    assert get_cmd.params_type is ParamsListChild


def test_get_run(test_pillar, param_spec):
    get_cmd = commands.Get.from_spec()
    param1 = 'some_param_gr/attr1'
    param2 = 'some_param_gr/attr2'
    param3 = 'some_param_gr2/attr1/8'
    param4 = 'some_param_gr2/attr1/some_key'

    get_cmd = commands.Get()
    res = get_cmd.run(str(param1), str(param2), str(param3), str(param4))

    _iter = iter(test_pillar)
    minion_id_1 = next(_iter)
    minion_id_2 = next(_iter)

    assert res == {
        minion_id_1: {
            param1: test_pillar[minion_id_1]['1']['2']['3'],
            param2: test_pillar[minion_id_1]['1']['2']['5'],
            param3: MISSED,
            param4: MISSED
        }, minion_id_2: {
            param1: test_pillar[minion_id_2]['1']['2']['3'],
            param2: test_pillar[minion_id_2]['1']['2']['5'],
            param3: test_pillar[minion_id_2]['1']['di_parent']['8'],
            param4: MISSED
        }
    }


def test_set_from_spec():
    states = {
        'pre': [
            'some.pre.state'
        ],
        'post': [
            'some.post.state'
        ],
    }
    get_cmd = commands.Set.from_spec(params_type='NTP', states=states)
    assert get_cmd.params_type is inputs.NTP
    assert get_cmd.pre_states == [State(st) for st in states['pre']]
    assert get_cmd.post_states == [State(st) for st in states['post']]


def test_set_run(monkeypatch, some_param_gr):
    pre_states = [State('pre')]
    post_states = [State('post')]

    @attr.s(auto_attribs=True)
    class SomeParamGroup(some_param_gr):
        attr3: str = inputs.ParamGroupInputBase._attr_ib(
            some_param_gr._param_group, default=''
        )

        @attr3.validator
        def _check_attr3(self, attribute, value):
            if type(value) is not str:
                raise TypeError('attr3 should be str')

    set_cmd = commands.Set(SomeParamGroup, pre_states, post_states)
    input_param = SomeParamGroup('new-value1', 'new-value2')

    calls = []

    apply_error = None
    post_apply_error = None

    # TODO consider to use mocks (e.g. pytest-mock plugin)
    @attr.s(auto_attribs=True)
    class PillarUpdater:
        targets: str = ALL_MINIONS

        def update(self, *args, **kwargs):
            calls.append((PillarUpdater.update, args, kwargs))

        def apply(self, *args, **kwargs):
            nonlocal apply_error
            calls.append((PillarUpdater.apply, args, kwargs))
            if apply_error:
                _error = apply_error
                apply_error = None
                raise _error

        def rollback(self, *args, **kwargs):
            calls.append((PillarUpdater.rollback, args, kwargs))

    class StatesApplier:
        @staticmethod
        def apply(*args, **kwargs):
            nonlocal post_apply_error
            calls.append((StatesApplier.apply, args, kwargs))
            if post_apply_error and args == (post_states,):
                _error = post_apply_error
                post_apply_error = None
                raise _error

    monkeypatch.setattr(
        commands, 'PillarUpdater', PillarUpdater
    )

    monkeypatch.setattr(
        commands, 'StatesApplier', StatesApplier
    )

    # dry run
    #   performs validation
    with pytest.raises(TypeError) as excinfo:
        set_cmd.run(1, 2, 3, dry_run=True)
    assert str(excinfo.value) == 'attr3 should be str'
    assert not calls

    #   performs validation
    set_cmd.run(input_param, dry_run=True)
    assert not calls

    # happy path
    set_cmd.run(input_param)
    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]

    # error during refresh
    calls[:] = []
    apply_error = RuntimeError

    with pytest.raises(apply_error):
        set_cmd.run(input_param)

    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (PillarUpdater.rollback, (), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]

    # error during post apply
    calls[:] = []
    apply_error = None
    post_apply_error = KeyError

    with pytest.raises(post_apply_error):
        set_cmd.run(input_param)

    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
        (PillarUpdater.rollback, (), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]


def test_eosupdate_run(monkeypatch):
    calls = []
    eosupdate_cmd = commands.EOSUpdate()

    # TODO consider to use mocks (e.g. pytest-mock plugin)
    class StatesApplier:
        @staticmethod
        def apply(*args, **kwargs):
            calls.append((StatesApplier.apply, args, kwargs))

    class YumRollbackManager:
        def __init__(self, *args, **kwargs):
            calls.append((YumRollbackManager.__init__, args, kwargs))

        def __enter__(self):
            calls.append((YumRollbackManager.__enter__,))

        def __exit__(self, *args, **kwargs):
            calls.append((YumRollbackManager.__exit__,))

    @property
    def last_txn_ids(self):
        return self._last_txn_ids

    monkeypatch.setattr(
        commands, 'StatesApplier', StatesApplier
    )

    monkeypatch.setattr(
        commands, 'YumRollbackManager', YumRollbackManager
    )

    # happy path
    eosupdate_cmd.run('some-target')
    assert calls == [
        (
            YumRollbackManager.__init__,
            ('some-target',),
            {'multiple_targets_ok': True}
        ),
        (YumRollbackManager.__enter__,)
    ] + [
        (
            StatesApplier.apply, (
                ["components.{}.update".format(component)],
            ), {}
        ) for component in ('eoscore', 's3server', 'hare', 'sspl', 'csm')
    ] + [
        (YumRollbackManager.__exit__,)
    ]
