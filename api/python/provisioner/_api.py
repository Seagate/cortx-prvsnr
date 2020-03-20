import sys

from .salt import auth_init as _auth_init
from .api_spec import api_spec
from .runner import SimpleRunner


# TODO
# - cache of pillar files
# - logic of cache update (watchers ?)
# - async API
# - typing
#
# - rollback
# - action might require a set of preliminary steps - hard
#   to describe using generic spec (yaml)


def auth_init(username, password, eauth='pam'):
    return _auth_init(username, password, eauth=eauth)


def run(command: str, *args, nowait=False, **kwargs):
    # do not expect ad-hoc credentials here
    kwargs.pop('password', None)
    kwargs.pop('username', None)
    kwargs.pop('eauth', None)
    return SimpleRunner(nowait=nowait).run(command, *args, **kwargs)


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return run(fun, *args, **kwargs)
    return f


mod = sys.modules[__name__]
for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
