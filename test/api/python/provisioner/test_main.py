import pytest
import yaml

import attr
from typing import Any

from provisioner import __main__
from provisioner import serialize
from provisioner.__main__ import _run_cmd


@attr.s(auto_attribs=True)
class SomeCommand:
    res: Any = None

    def run(self, *args, **kwargs):
        if isinstance(self.res, Exception):
            raise self.res
        else:
            return self.res


@attr.s(auto_attribs=True)
class Outputter:
    res: Any = None

    def __call__(self, data):
        self.res = data


@pytest.fixture
def outputter(monkeypatch):
    _outputter = Outputter()
    monkeypatch.setattr(
        __main__, '_output', _outputter
    )
    return _outputter


@pytest.mark.parametrize("output_type", ['plain', 'json', 'yaml'])
def test_run_cmd_exc(outputter, output_type):
    exc = ValueError('some error')
    cmd = SomeCommand(exc)
    expected_exc_type = ValueError if output_type == 'plain' else SystemExit

    with pytest.raises(expected_exc_type) as excinfo:
        _run_cmd(cmd, output_type)

    if output_type == 'plain':
        assert excinfo.value is exc
    else:
        assert excinfo.value.code == 1

        if output_type == 'yaml':
            output = yaml.safe_load(outputter.res)
        else:  # json
            output = serialize.loads(outputter.res)

        if output_type == 'yaml':
            assert output == {
                'exc': {
                    'type': type(exc).__name__,
                    'args': list(exc.args)
                }
            }
        else:  # json
            assert list(output) == ['exc']
            assert output['exc'].args == exc.args


@pytest.mark.parametrize("output_type", ['plain', 'json', 'yaml'])
def test_run_cmd_ok(outputter, output_type):
    ret = {
        'some-key': 'some-value'
    }
    cmd = SomeCommand(ret)

    _run_cmd(cmd, output_type)

    if output_type == 'plain':
        assert outputter.res == str(ret)
    else:
        if output_type == 'yaml':
            output = yaml.safe_load(outputter.res)
        else:  # json
            output = serialize.loads(outputter.res)

        assert output == {
            'ret': ret,
        }
