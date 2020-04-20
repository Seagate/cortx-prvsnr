import attr
from functools import partial
from typing import Callable, Any, Tuple, Dict

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
