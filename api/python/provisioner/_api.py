import sys

from .config import ALL_MINIONS
from .salt import auth_init as _auth_init
from .api_spec import api_spec
from .commands import commands


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


def run(command: str, *args, targets: str = ALL_MINIONS, **kwargs):
    cmd = commands[command]
    return cmd.run(*args, targets=targets, **kwargs)


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return run(fun, *args, **kwargs)
    return f


mod = sys.modules[__name__]
for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
