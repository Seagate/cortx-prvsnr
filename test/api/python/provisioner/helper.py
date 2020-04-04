import attr
from functools import partial
from typing import Callable, Any, Tuple, Dict


@attr.s(auto_attribs=True)
class MockRes:
    res: Any
    args: Tuple
    kwargs: Dict

    @property
    def args_all(self):
        return (self.args, self.kwargs)


def mock_fun(mock, *args, mock_res=None, mock_key=None, **kwargs):
    res = (
        mock(*args, **kwargs) if isinstance(mock, Callable) else mock if mock
        else (args, kwargs)
    )

    if isinstance(mock_res, dict):
        if mock_key is None:
            mock_key = mock
        mock_res[mock_key] = MockRes(res, args, kwargs)

    return res


def mock_fun_echo(mock_res=None, mock_key=None):
    return partial(mock_fun, None, mock_res=mock_res, mock_key=mock_key)


def mock_fun_result(res, mock_res=None, mock_key=None):
    return partial(mock_fun, res, mock_res=mock_res, mock_key=mock_key)
